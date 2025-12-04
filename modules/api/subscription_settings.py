import logging
from typing import Any, Dict, Optional
from modules.api.client import RemnaAPI

logger = logging.getLogger(__name__)


class SubscriptionSettingsAPI:
    """API methods for subscription settings (Remnawave API v2.2.6)"""

    @staticmethod
    async def get_settings():
        """Get subscription settings"""
        return await RemnaAPI.get("subscription-settings")

    @staticmethod
    async def update_settings(data: Dict[str, Any]):
        """Update subscription settings"""
        return await RemnaAPI.patch("subscription-settings", data)
