from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging

from modules.config import MAIN_MENU, USER_MENU, NODE_MENU, STATS_MENU, HOST_MENU, INBOUND_MENU, BULK_MENU, CREATE_USER, CREATE_USER_FIELD, SELECTING_USER

logger = logging.getLogger(__name__)
from modules.utils.auth import check_authorization, get_user_role, is_admin_user
from modules.handlers.users import show_users_menu, start_create_user, show_user_details
from modules.handlers.nodes import show_nodes_menu
from modules.handlers.stats import show_stats_menu
from modules.handlers.hosts import show_hosts_menu
from modules.handlers.inbounds import show_inbounds_menu, handle_inbounds_menu
from modules.handlers.bulk import show_bulk_menu
from modules.handlers.core.start import show_main_menu
from modules.handlers.ssh.handlers import start_ssh_flow
from modules.handlers.core.language import (
    LANGUAGE_MENU_CALLBACK,
    LANGUAGE_SELECT_PREFIX,
    handle_language_selection,
    show_language_menu,
)

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu selection"""
    # Проверяем авторизацию
    if not check_authorization(update.effective_user):
        await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()

    role = get_user_role(update.effective_user.id)
    is_admin = is_admin_user(update.effective_user.id)
    context.user_data['role'] = role
    context.user_data['is_admin'] = is_admin

    data = query.data
    admin_only_actions = {"bulk", "menu_bulk", "create_user", "menu_create_user"}
    if data in admin_only_actions and not is_admin:
        await query.answer("Этот раздел доступен только администраторам.", show_alert=True)
        return MAIN_MENU

    logger.info(f"=== MENU SELECTION HANDLER ===")
    logger.info(f"Handling menu callback: {data}")
    logger.info(f"Current state: {context.user_data.get('conversation_state', 'unknown')}")
    logger.info(f"==============================")

    if data == "users" or data == "menu_users":
        await show_users_menu(update, context)
        return USER_MENU

    elif data == "nodes" or data == "menu_nodes":
        await show_nodes_menu(update, context)
        return NODE_MENU

    elif data == "stats" or data == "menu_stats":
        await show_stats_menu(update, context)
        return STATS_MENU

    elif data == "hosts" or data == "menu_hosts":
        await show_hosts_menu(update, context)
        return HOST_MENU

    elif data == "inbounds" or data == "menu_inbounds":
        await show_inbounds_menu(update, context)
        return INBOUND_MENU

    elif data == LANGUAGE_MENU_CALLBACK:
        await show_language_menu(update, context)
        return MAIN_MENU

    # Handle inbound menu callbacks (temporary fix)
    elif data in ["list_inbounds", "list_full_inbounds", "list_inbounds_stats", "filter_inbounds", "refresh_inbounds", "debug_users"]:
        logger.info(f"Redirecting inbound callback to handle_inbounds_menu: {data}")
        return await handle_inbounds_menu(update, context)

    elif data == "bulk" or data == "menu_bulk":
        await show_bulk_menu(update, context)
        return BULK_MENU

    elif data == "create_user" or data == "menu_create_user":
        await start_create_user(update, context)
        return CREATE_USER_FIELD

    elif data == "ssh" or data == "menu_ssh":
        # Start SSH connection flow
        return await start_ssh_flow(update, context)

    elif data == "back_to_main":
        await show_main_menu(update, context)
        return MAIN_MENU

    elif data.startswith("view_"):
        uuid = data.split("_")[1]
        await show_user_details(update, context, uuid)
        return SELECTING_USER

    elif data.startswith(LANGUAGE_SELECT_PREFIX):
        return await handle_language_selection(update, context)

    return MAIN_MENU

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu with authorization check"""
    # Проверяем авторизацию
    if not check_authorization(update.effective_user):
        await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        return ConversationHandler.END
    
    # Показываем главное меню со статистикой
    await show_main_menu(update, context)
    return MAIN_MENU



