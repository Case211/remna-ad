import io
import logging
from typing import Optional

from modules.config import (
    ADMIN_NOTIFICATIONS_ENABLED,
    ADMIN_NOTIFICATIONS_CHAT_ID,
    ADMIN_NOTIFICATIONS_THREAD_ID,
    ADMIN_NOTIFICATIONS_TICKETS_THREAD_ID,
)

logger = logging.getLogger(__name__)


def _resolve_thread_id(for_tickets: bool = False) -> Optional[int]:
    if for_tickets and ADMIN_NOTIFICATIONS_TICKETS_THREAD_ID:
        return ADMIN_NOTIFICATIONS_TICKETS_THREAD_ID
    return ADMIN_NOTIFICATIONS_THREAD_ID


async def send_admin_message(bot, text: str, for_tickets: bool = False) -> bool:
    if not ADMIN_NOTIFICATIONS_ENABLED or not ADMIN_NOTIFICATIONS_CHAT_ID:
        return False
    try:
        kwargs = {}
        tid = _resolve_thread_id(for_tickets)
        if tid:
            kwargs["message_thread_id"] = tid
        await bot.send_message(chat_id=ADMIN_NOTIFICATIONS_CHAT_ID, text=text, **kwargs)
        return True
    except Exception:
        logger.debug("Failed to send admin message", exc_info=True)
        return False


async def send_admin_document(bot, data: bytes, filename: str, caption: Optional[str] = None, for_tickets: bool = False) -> bool:
    if not ADMIN_NOTIFICATIONS_ENABLED or not ADMIN_NOTIFICATIONS_CHAT_ID:
        return False
    try:
        bio = io.BytesIO(data)
        bio.name = filename
        kwargs = {}
        tid = _resolve_thread_id(for_tickets)
        if tid:
            kwargs["message_thread_id"] = tid
        await bot.send_document(chat_id=ADMIN_NOTIFICATIONS_CHAT_ID, document=bio, caption=caption or "", **kwargs)
        return True
    except Exception:
        logger.debug("Failed to send admin document", exc_info=True)
        return False

