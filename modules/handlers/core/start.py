from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from modules.config import (
    MAIN_MENU, DASHBOARD_SHOW_SYSTEM_STATS, DASHBOARD_SHOW_SERVER_INFO,
    DASHBOARD_SHOW_USERS_COUNT, DASHBOARD_SHOW_NODES_COUNT, 
    DASHBOARD_SHOW_TRAFFIC_STATS, DASHBOARD_SHOW_UPTIME
)
from modules.utils.auth import (
    check_operator_or_admin,
    get_user_role,
    is_admin_user
)
from modules.api.users import UserAPI
from modules.api.nodes import NodeAPI
from modules.api.inbounds import InboundAPI
from modules.handlers.core.language import LANGUAGE_MENU_CALLBACK
from modules.localization import SUPPORTED_LANGUAGES, get_user_language
from modules.utils.formatters import format_bytes
import logging

logger = logging.getLogger(__name__)

ROLE_DISPLAY = {"admin": "Администратор", "operator": "Оператор"}

@check_operator_or_admin
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    await show_main_menu(update, context)
    return MAIN_MENU

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu with system statistics"""
    user = update.effective_user or (update.callback_query.from_user if update.callback_query else None)
    role = get_user_role(user.id) if user else None
    context.user_data['role'] = role
    is_admin = is_admin_user(user.id) if user else False
    current_language = get_user_language(context)
    language_label = SUPPORTED_LANGUAGES.get(current_language, SUPPORTED_LANGUAGES.get('ru', 'Русский'))

    keyboard = [
        [InlineKeyboardButton("👥 Управление пользователями", callback_data="users")],
        [InlineKeyboardButton("🖥️ Управление серверами", callback_data="nodes")],
        [InlineKeyboardButton("📊 Статистика системы", callback_data="stats")],
        [InlineKeyboardButton("🌐 Управление хостами", callback_data="hosts")],
        [InlineKeyboardButton("🔌 Управление Inbounds", callback_data="inbounds")],
        [InlineKeyboardButton("🌐 Язык бота", callback_data=LANGUAGE_MENU_CALLBACK)]
    ]

    if is_admin:
        keyboard.append([InlineKeyboardButton("🔄 Массовые операции", callback_data="bulk")])
        keyboard.append([InlineKeyboardButton("➕ Создать пользователя", callback_data="create_user")])

        keyboard.append([InlineKeyboardButton("SSH", callback_data="ssh")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Получаем статистику системы
    stats_text = await get_system_stats()
    
    message = "🎛️ *Главное меню Remnawave Admin*\n\n"
    message += stats_text + "\n"
    message += f"🌐 Текущий язык: {language_label}\n\n"
    message += "Выберите раздел для управления:"

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def get_system_stats():
    """Get system statistics based on configuration settings"""
    stats_sections = []
    
    try:
        # Системная информация (если включена)
        if DASHBOARD_SHOW_SYSTEM_STATS:
            try:
                # Используем данные из API для консистентности
                from modules.api.system import SystemAPI
                
                stats = await SystemAPI.get_stats()
                if stats:
                    # CPU Information
                    cpu_cores = stats['cpu']['cores']
                    cpu_physical_cores = stats['cpu']['physicalCores']
                    
                    # Memory Information with correct calculation
                    total_mem = stats['memory']['total']
                    free_mem = stats['memory']['free']
                    available_mem = stats['memory'].get('available', free_mem)
                    
                    # Correct memory calculation for Linux systems
                    used_mem = total_mem - available_mem
                    used_percent = (used_mem / total_mem) * 100 if total_mem > 0 else 0
                    
                    system_stats = f"🖥️ *Система*:\n"
                    system_stats += f"  • CPU: {cpu_cores} ядер ({cpu_physical_cores} физ.)\n"
                    system_stats += f"  • RAM: {format_bytes(used_mem)} / {format_bytes(total_mem)} ({used_percent:.1f}%)\n"
                    
                    if DASHBOARD_SHOW_UPTIME:
                        uptime_seconds = int(stats['uptime'])
                        uptime_days = uptime_seconds // (24 * 3600)
                        uptime_hours = (uptime_seconds % (24 * 3600)) // 3600
                        uptime_minutes = (uptime_seconds % 3600) // 60
                        system_stats += f"  • Uptime: {uptime_days}д {uptime_hours}ч {uptime_minutes}м\n"
                    
                    stats_sections.append(system_stats)
                else:
                    # Fallback to psutil if API fails
                    import psutil
                    from datetime import datetime
                    
                    cpu_cores = psutil.cpu_count()
                    cpu_physical_cores = psutil.cpu_count(logical=False)
                    memory = psutil.virtual_memory()
                    
                    system_stats = f"🖥️ *Система*:\n"
                    system_stats += f"  • CPU: {cpu_cores} ядер ({cpu_physical_cores} физ.)\n"
                    system_stats += f"  • RAM: {format_bytes(memory.used)} / {format_bytes(memory.total)} ({memory.percent:.1f}%)\n"
                    
                    if DASHBOARD_SHOW_UPTIME:
                        uptime_seconds = psutil.boot_time()
                        current_time = datetime.now().timestamp()
                        uptime = int(current_time - uptime_seconds)
                        uptime_days = uptime // (24 * 3600)
                        uptime_hours = (uptime % (24 * 3600)) // 3600
                        uptime_minutes = (uptime % 3600) // 60
                        system_stats += f"  • Uptime: {uptime_days}д {uptime_hours}ч {uptime_minutes}м\n"
                    
                    stats_sections.append(system_stats)
                
            except Exception as e:
                logger.error(f"Error getting system stats: {e}")
        
        # Статистика пользователей (если включена)
        if DASHBOARD_SHOW_USERS_COUNT:
            try:
                users_response = await UserAPI.get_all_users()
                users_count = 0
                user_stats = {'ACTIVE': 0, 'DISABLED': 0, 'LIMITED': 0, 'EXPIRED': 0}
                total_traffic = 0
                
                if users_response:
                    users = []
                    if isinstance(users_response, dict):
                        if 'users' in users_response:
                            users = users_response['users']
                        elif 'response' in users_response and 'users' in users_response['response']:
                            users = users_response['response']['users']
                    elif isinstance(users_response, list):
                        users = users_response
                    
                    users_count = len(users)
                    
                    for user in users:
                        status = user.get('status', 'UNKNOWN')
                        if status in user_stats:
                            user_stats[status] += 1
                        
                        if DASHBOARD_SHOW_TRAFFIC_STATS:
                            traffic_bytes = user.get('usedTrafficBytes', 0)
                            if isinstance(traffic_bytes, (int, float)):
                                total_traffic += traffic_bytes
                            elif isinstance(traffic_bytes, str) and traffic_bytes.isdigit():
                                total_traffic += int(traffic_bytes)
                
                user_section = f"👥 *Пользователи* ({users_count} всего):\n"
                for status, count in user_stats.items():
                    if count > 0:
                        emoji = {"ACTIVE": "✅", "DISABLED": "❌", "LIMITED": "⚠️", "EXPIRED": "⏰"}.get(status, "❓")
                        user_section += f"  • {emoji} {status}: {count}\n"
                
                if DASHBOARD_SHOW_TRAFFIC_STATS and total_traffic > 0:
                    user_section += f"  • Общий трафик: {format_bytes(total_traffic)}\n"
                
                stats_sections.append(user_section)
                
            except Exception as e:
                logger.error(f"Error getting user stats: {e}")
        
        # Статистика узлов (если включена)
        if DASHBOARD_SHOW_NODES_COUNT:
            try:
                nodes_response = await NodeAPI.get_all_nodes()
                nodes_count = 0
                online_nodes = 0
                
                if nodes_response:
                    nodes = []
                    if isinstance(nodes_response, dict):
                        if 'nodes' in nodes_response:
                            nodes = nodes_response['nodes']
                        elif 'response' in nodes_response and 'nodes' in nodes_response['response']:
                            nodes = nodes_response['response']['nodes']
                    elif isinstance(nodes_response, list):
                        nodes = nodes_response
                    
                    nodes_count = len(nodes)
                    online_nodes = sum(1 for node in nodes if node.get('isConnected'))
                
                node_section = f"🖥️ *Серверы*: {online_nodes}/{nodes_count} онлайн\n"
                stats_sections.append(node_section)
                
            except Exception as e:
                logger.error(f"Error getting node stats: {e}")
        
        # Статистика трафика в реальном времени (если включена)
        if DASHBOARD_SHOW_TRAFFIC_STATS:
            try:
                realtime_usage = await NodeAPI.get_nodes_realtime_usage()
                if realtime_usage and len(realtime_usage) > 0:
                    total_download_speed = 0
                    total_upload_speed = 0
                    total_download_bytes = 0
                    total_upload_bytes = 0
                    
                    for node_data in realtime_usage:
                        total_download_speed += node_data.get('downloadSpeedBps', 0)
                        total_upload_speed += node_data.get('uploadSpeedBps', 0)
                        total_download_bytes += node_data.get('downloadBytes', 0)
                        total_upload_bytes += node_data.get('uploadBytes', 0)
                    
                    total_speed = total_download_speed + total_upload_speed
                    total_bytes = total_download_bytes + total_upload_bytes
                    
                    if total_speed > 0 or total_bytes > 0:
                        traffic_section = f"📊 *Текущая активность серверов*:\n"
                        if total_speed > 0:
                            traffic_section += f"  • Общая скорость: {format_bytes(total_speed)}/с\n"
                            traffic_section += f"  • Скачивание: {format_bytes(total_download_speed)}/с\n"
                            traffic_section += f"  • Загрузка: {format_bytes(total_upload_speed)}/с\n"
                        if total_bytes > 0:
                            traffic_section += f"  • Всего скачано: {format_bytes(total_download_bytes)}\n"
                            traffic_section += f"  • Всего загружено: {format_bytes(total_upload_bytes)}\n"
                        
                        stats_sections.append(traffic_section)
                        
            except Exception as e:
                logger.warning(f"Could not get realtime server stats: {e}")
        
        # Информация о серверах (если включена)
        if DASHBOARD_SHOW_SERVER_INFO:
            try:
                inbounds_response = await InboundAPI.get_inbounds()
                inbounds_count = 0
                
                if inbounds_response:
                    inbounds = []
                    if isinstance(inbounds_response, dict):
                        if 'inbounds' in inbounds_response:
                            inbounds = inbounds_response['inbounds']
                        elif 'response' in inbounds_response and 'inbounds' in inbounds_response['response']:
                            inbounds = inbounds_response['response']['inbounds']
                    elif isinstance(inbounds_response, list):
                        inbounds = inbounds_response
                    
                    inbounds_count = len(inbounds)
                
                server_section = f"🔌 *Inbound'ы*: {inbounds_count} шт.\n"
                stats_sections.append(server_section)
                
            except Exception as e:
                logger.error(f"Error getting inbound stats: {e}")
        
        # Собираем все секции в одну строку
        if stats_sections:
            result = "📈 *Системная статистика*\n\n" + "\n".join(stats_sections)
        else:
            result = "📈 *Статистика*\n\nОтображение статистики отключено в настройках."
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return "📈 *Статистика временно недоступна*\n"


async def get_basic_system_stats():
    """Get basic system statistics (fallback version)"""
    try:
        # Получаем статистику пользователей
        users_response = await UserAPI.get_all_users()
        users_count = 0
        active_users = 0
        if users_response:
            # Проверяем разные возможные структуры ответа
            users = []
            if isinstance(users_response, dict):
                if 'users' in users_response:
                    users = users_response['users']
                elif 'response' in users_response and 'users' in users_response['response']:
                    users = users_response['response']['users']
            elif isinstance(users_response, list):
                users = users_response
            
            users_count = len(users)
            active_users = sum(1 for user in users if user.get('status') == 'ACTIVE')

        # Получаем статистику узлов
        nodes_response = await NodeAPI.get_all_nodes()
        nodes_count = 0
        online_nodes = 0
        if nodes_response:
            # Проверяем разные возможные структуры ответа
            nodes = []
            if isinstance(nodes_response, dict):
                if 'nodes' in nodes_response:
                    nodes = nodes_response['nodes']
                elif 'response' in nodes_response and 'nodes' in nodes_response['response']:
                    nodes = nodes_response['response']['nodes']
            elif isinstance(nodes_response, list):
                nodes = nodes_response
            
            nodes_count = len(nodes)
            online_nodes = sum(1 for node in nodes if node.get('isConnected'))

        # Получаем статистику inbound'ов
        inbounds_response = await InboundAPI.get_inbounds()
        inbounds_count = 0
        if inbounds_response:
            # Проверяем разные возможные структуры ответа
            inbounds = []
            if isinstance(inbounds_response, dict):
                if 'inbounds' in inbounds_response:
                    inbounds = inbounds_response['inbounds']
                elif 'response' in inbounds_response and 'inbounds' in inbounds_response['response']:
                    inbounds = inbounds_response['response']['inbounds']
            elif isinstance(inbounds_response, list):
                inbounds = inbounds_response
            
            inbounds_count = len(inbounds)

        # Формируем текст статистики
        stats = f"📈 *Общая статистика системы:*\n"
        stats += f"👥 Пользователи: {active_users}/{users_count}\n"
        
        # Получаем текущую статистику трафика по серверам
        try:
            realtime_usage = await NodeAPI.get_nodes_realtime_usage()
            if realtime_usage and len(realtime_usage) > 0:
                # Суммируем данные по всем серверам
                total_download_speed = 0
                total_upload_speed = 0
                total_download_bytes = 0
                total_upload_bytes = 0
                
                for node_data in realtime_usage:
                    total_download_speed += node_data.get('downloadSpeedBps', 0)
                    total_upload_speed += node_data.get('uploadSpeedBps', 0)
                    total_download_bytes += node_data.get('downloadBytes', 0)
                    total_upload_bytes += node_data.get('uploadBytes', 0)
                
                total_speed = total_download_speed + total_upload_speed
                total_bytes = total_download_bytes + total_upload_bytes
                
                if total_speed > 0 or total_bytes > 0:
                    stats += f"\n📊 *Текущая активность серверов*:\n"
                    if total_speed > 0:
                        stats += f"  • Общая скорость: {format_bytes(total_speed)}/с\n"
                        stats += f"  • Скачивание: {format_bytes(total_download_speed)}/с\n"
                        stats += f"  • Загрузка: {format_bytes(total_upload_speed)}/с\n"
                    if total_bytes > 0:
                        stats += f"  • Всего скачано: {format_bytes(total_download_bytes)}\n"
                        stats += f"  • Всего загружено: {format_bytes(total_upload_bytes)}\n"
        except Exception as e:
            logger.warning(f"Could not get realtime server stats: {e}")
        
        stats += f"\n🖥️ Узлы: {online_nodes}/{nodes_count} онлайн\n"
        stats += f"🔌 Inbound'ы: {inbounds_count} шт.\n"
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting basic system stats: {e}")
        return "📈 *Статистика временно недоступна*\n"



