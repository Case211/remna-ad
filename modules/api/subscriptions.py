import logging
from typing import Any, Dict, List, Optional
from modules.api.client import RemnaAPI

logger = logging.getLogger(__name__)


class SubscriptionAPI:
    """API methods for subscriptions (Remnawave API v2.2.6)"""

    @staticmethod
    async def list_subscriptions(params: Optional[Dict[str, Any]] = None):
        """List subscriptions"""
        return await RemnaAPI.get("subscriptions", params=params or {})

    @staticmethod
    async def get_by_uuid(uuid: str):
        """Get subscription by UUID"""
        return await RemnaAPI.get(f"subscriptions/by-uuid/{uuid}")

    @staticmethod
    async def get_by_username(username: str):
        """Get subscription by username"""
        return await RemnaAPI.get(f"subscriptions/by-username/{username}")

    @staticmethod
    async def get_by_short_uuid(short_uuid: str):
        """Get subscription by short UUID"""
        return await RemnaAPI.get(f"subscriptions/by-short-uuid/{short_uuid}")

    @staticmethod
    async def get_raw_by_short_uuid(short_uuid: str):
        """Get raw subscription by short UUID (returns subscription content)"""
        return await RemnaAPI.get(f"subscriptions/by-short-uuid/{short_uuid}/raw")
