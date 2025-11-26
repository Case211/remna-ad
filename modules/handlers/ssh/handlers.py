import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.config import (
    SSH_START, SSH_HOST, SSH_LOGIN, SSH_PASSWORD, SSH_MENU, SSH_SHELL, SSH_CMD,
    SSH_ADD_NAME, SSH_ADD_DESC, SSH_ADD_CMD,
    MAIN_MENU,
    SSH_OUTPUT_CHAT_ID, SSH_OUTPUT_THREAD_ID,
)
from modules.utils.auth import check_operator_or_admin
from modules.ssh.client import connect_interactive
from modules.ssh.session_store import SSH_SESSIONS
from modules.ssh.repos import (
    get_repositories,
    get_all_repositories_for_user,
    add_favorite_repository,
    get_favorite_repositories,
)


logger = logging.getLogger(__name__)


def _kb_exit():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Exit SSH", callback_data="ssh_exit")]])



@check_operator_or_admin
async def start_ssh_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    await _send(update, "Введите IP или login@ip для подключения по SSH (порт 22 по умолчанию).\nПример: root@1.2.3.4 или 1.2.3.4")
    return SSH_HOST


async def handle_host_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Parse login@host or just host
    m = re.match(r"^(?:(?P<login>[a-zA-Z0-9_.-]+)@)?(?P<host>[^\s]+)$", text)
    if not m:
        await update.message.reply_text("Некорректный формат. Введите IP или login@ip.")
        return SSH_HOST

    host = m.group("host")
    login = m.group("login")
    context.user_data['ssh_host'] = host
    if login:
        context.user_data['ssh_login'] = login
        await update.message.reply_text("Введите пароль пользователя:")
        return SSH_PASSWORD
    else:
        await update.message.reply_text("Введите логин пользователя:")
        return SSH_LOGIN


async def handle_login_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    login = update.message.text.strip()
    if not login:
        await update.message.reply_text("Логин не может быть пустым. Введите логин пользователя:")
        return SSH_LOGIN
    context.user_data['ssh_login'] = login
    await update.message.reply_text("Введите пароль пользователя:")
    return SSH_PASSWORD


async def handle_password_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    host = context.user_data.get('ssh_host')
    login = context.user_data.get('ssh_login')

    # Do not log password
    logger.info(f"SSH connecting to {login}@{host}")

    session = await connect_interactive(host=host, username=login, password=password)
    if not session:
        await update.message.reply_text("Не удалось подключиться. Проверьте IP/логин/пароль и доступ по SSH.")
        return SSH_HOST

    await SSH_SESSIONS.put(update.effective_chat.id, session)

    # Start streaming shell output in background (respect topic/thread if any)
    thread_id = getattr(update.message, 'message_thread_id', None)
    await session.start_reader(update.get_bot(), update.effective_chat.id, thread_id=thread_id)

    # Show SSH menu (repos or custom command)
    await show_ssh_menu(update, context, connected=True)
    return SSH_MENU


async def handle_shell_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.strip().lower() in ("/exit", "exit", "logout", "quit"):
        return await handle_exit(update, context)

    sess = await SSH_SESSIONS.get(update.effective_chat.id)
    if not sess or not sess.connected:
        await update.message.reply_text("Сессия не активна. Начните новое подключение.")
        return SSH_HOST
    await sess.send_line(text)
    return SSH_SHELL


async def show_ssh_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, connected: bool = False):
    user_id = update.effective_user.id
    repos = get_all_repositories_for_user(user_id)
    buttons = []
    # Add repo button
    buttons.append([InlineKeyboardButton("Добавить репозиторий", callback_data="ssh_add_repo")])
    # Build repo buttons
    fav_ids = {r.id for r in get_favorite_repositories(user_id)}
    for repo in repos:
        label = f"⭐ {repo.name}" if repo.id in fav_ids else repo.name
        buttons.append([InlineKeyboardButton(label, callback_data=f"ssh_repo_{repo.id}")])
    # Add custom command & exit
    buttons.append([InlineKeyboardButton("Своя команда", callback_data="ssh_custom")])
    buttons.append([InlineKeyboardButton("Exit SSH", callback_data="ssh_exit")])

    text = "SSH подключен. Выберите репозиторий для установки или введите произвольную команду."
    if not connected:
        # For callbacks
        if update.callback_query:
            await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))
            return
    # For new messages
    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))


async def handle_ssh_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "ssh_custom":
        await query.edit_message_text("Введите команду для выполнения на сервере:", reply_markup=_kb_exit())
        return SSH_CMD

    if data == "ssh_add_repo":
        await query.edit_message_text("Введите имя репозитория:", reply_markup=_kb_exit())
        return SSH_ADD_NAME

    if data.startswith("ssh_repo_"):
        repo_id = data[len("ssh_repo_"):]
        repo = next((r for r in get_repositories() if r.id == repo_id), None)
        if not repo:
            await query.edit_message_text("Репозиторий не найден.", reply_markup=_kb_exit())
            return SSH_MENU
        # Start interactive command process for repo
        sess = await SSH_SESSIONS.get(update.effective_chat.id)
        if not sess:
            await query.edit_message_text("Сессия не активна.", reply_markup=_kb_exit())
            return SSH_HOST
        thread_id = getattr(query.message, 'message_thread_id', None)
        ok = await sess.start_command(query.get_bot(), update.effective_chat.id, repo.command, thread_id=thread_id)
        if not ok:
            await query.edit_message_text("Не удалось запустить установку.", reply_markup=_kb_exit())
            return SSH_MENU
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Остановить", callback_data="ssh_stop")],
            [InlineKeyboardButton("Отправить вывод файлом", callback_data="ssh_sendfile")],
            [InlineKeyboardButton("В меню SSH", callback_data="ssh_menu")],
        ])
        await query.edit_message_text(
            f"Запущена установка: {repo.name}\nВывод будет приходить сюда.\nОтвечайте на вопросы скрипта сообщениями в чат.",
            reply_markup=kb,
        )
        return SSH_CMD

    if data == "ssh_menu":
        await show_ssh_menu(update, context)
        return SSH_MENU

    if data == "ssh_stop":
        sess = await SSH_SESSIONS.get(update.effective_chat.id)
        if not sess:
            await query.edit_message_text("Сессия не активна.", reply_markup=_kb_exit())
            return SSH_HOST
        data_bytes = await sess.stop_command()
        if data_bytes:
            await _send_output_file(query, data_bytes, filename_prefix="ssh-output")
        await show_ssh_menu(update, context)
        return SSH_MENU

    if data == "ssh_sendfile":
        sess = await SSH_SESSIONS.get(update.effective_chat.id)
        if not sess:
            await query.edit_message_text("Сессия не активна.", reply_markup=_kb_exit())
            return SSH_HOST
        # Snapshot current output without stopping the command
        data_bytes = sess.snapshot_command_output()
        if data_bytes:
            await _send_output_file(query, data_bytes, filename_prefix="ssh-output")
        await show_ssh_menu(update, context)
        return SSH_MENU

    if data == "ssh_exit":
        return await handle_exit(update, context)

    return SSH_MENU


async def handle_custom_command_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text.strip()
    if not cmd:
        await update.message.reply_text("Команда не может быть пустой. Введите команду:")
        return SSH_CMD
    sess = await SSH_SESSIONS.get(update.effective_chat.id)
    if not sess:
        await update.message.reply_text("Сессия не активна.")
        return SSH_HOST
    thread_id = getattr(update.message, 'message_thread_id', None)
    ok = await sess.start_command(update.get_bot(), update.effective_chat.id, cmd, thread_id=thread_id)
    if not ok:
        await update.message.reply_text("Не удалось запустить команду.")
        return SSH_MENU
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Остановить", callback_data="ssh_stop")],
        [InlineKeyboardButton("Отправить вывод файлом", callback_data="ssh_sendfile")],
        [InlineKeyboardButton("В меню SSH", callback_data="ssh_menu")],
    ])
    await update.message.reply_text("Команда запущена. Отвечайте на вопросы скрипта сообщениями.", reply_markup=kb)
    return SSH_CMD


async def handle_add_repo_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.message.text or '').strip()
    if not name:
        await update.message.reply_text("Имя не может быть пустым. Введите имя репозитория:")
        return SSH_ADD_NAME
    context.user_data['add_repo_name'] = name
    await update.message.reply_text("Введите описание репозитория:")
    return SSH_ADD_DESC


async def handle_add_repo_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = (update.message.text or '').strip()
    context.user_data['add_repo_desc'] = desc
    await update.message.reply_text("Введите команду установки:")
    return SSH_ADD_CMD


async def handle_add_repo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = (update.message.text or '').strip()
    if not cmd:
        await update.message.reply_text("Команда не может быть пустой. Введите команду установки:")
        return SSH_ADD_CMD
    name = context.user_data.get('add_repo_name')
    desc = context.user_data.get('add_repo_desc', '')
    repo = add_favorite_repository(update.effective_user.id, name, desc, cmd)
    # Clear temp data
    context.user_data.pop('add_repo_name', None)
    context.user_data.pop('add_repo_desc', None)
    await update.message.reply_text(f"Сохранено в избранное: {repo.name}")
    await show_ssh_menu(update, context)
    return SSH_MENU


async def handle_cmd_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.strip().lower() in ("/exit", "exit", "logout", "quit"):
        return await handle_exit(update, context)
    sess = await SSH_SESSIONS.get(update.effective_chat.id)
    if not sess:
        await update.message.reply_text("Сессия не активна.")
        return SSH_HOST
    ok = await sess.send_to_command(text)
    if not ok:
        await update.message.reply_text("Команда не активна. Вернитесь в меню SSH.")
        return SSH_MENU
    return SSH_CMD


async def handle_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await SSH_SESSIONS.close(update.effective_chat.id)
    await _send(update, "SSH-сессия закрыта.")
    return MAIN_MENU


async def _send(update: Update, text: str):
    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=_kb_exit())
    else:
        await update.message.reply_text(text)


async def _send_output_file(query_or_update, data: bytes, filename_prefix: str = "output"):
    import io
    from datetime import datetime
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    bio = io.BytesIO(data)
    bio.name = f"{filename_prefix}_{ts}.txt"
    # Resolve bot
    bot = query_or_update.get_bot() if hasattr(query_or_update, 'get_bot') else getattr(query_or_update, 'bot', None)
    # Destination: prefer configured SSH output chat/thread
    chat_id = SSH_OUTPUT_CHAT_ID
    thread_id = SSH_OUTPUT_THREAD_ID
    # Fallback to current chat/thread if not configured
    if not chat_id:
        if hasattr(query_or_update, 'effective_chat') and query_or_update.effective_chat:
            chat_id = query_or_update.effective_chat.id
    if thread_id is None:
        if hasattr(query_or_update, 'effective_message') and query_or_update.effective_message:
            thread_id = getattr(query_or_update.effective_message, 'message_thread_id', None)
    try:
        if thread_id:
            await bot.send_document(chat_id=chat_id, message_thread_id=thread_id, document=bio, caption="Полный вывод команды")
        else:
            await bot.send_document(chat_id=chat_id, document=bio, caption="Полный вывод команды")
    except Exception:
        logger.debug("Failed to send output document", exc_info=True)
