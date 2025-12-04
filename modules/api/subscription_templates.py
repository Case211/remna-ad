import logging
from typing import Any, Dict, Optional
from modules.api.client import RemnaAPI

logger = logging.getLogger(__name__)


class SubscriptionTemplateAPI:
    """API methods for subscription templates (Remnawave API v2.2.6)"""

    @staticmethod
    async def list_templates(params: Optional[Dict[str, Any]] = None):
        """Get all subscription templates"""
        return await RemnaAPI.get("subscription-templates", params=params or {})

    @staticmethod
    async def get_template(uuid: str):
        """Get subscription template by UUID"""
        return await RemnaAPI.get(f"subscription-templates/{uuid}")

    @staticmethod
    async def create_template(data: Dict[str, Any]):
        """Create subscription template"""
        return await RemnaAPI.post("subscription-templates", data)

    @staticmethod
    async def update_template(data: Dict[str, Any]):
        """Update subscription template"""
        return await RemnaAPI.patch("subscription-templates", data)

    @staticmethod
    async def delete_template(uuid: str):
        """Delete subscription template"""
        return await RemnaAPI.delete(f"subscription-templates/{uuid}")
