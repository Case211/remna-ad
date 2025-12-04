import logging
from typing import Optional
from modules.api.client import RemnaAPI

logger = logging.getLogger(__name__)


class SubscriptionLinkAPI:
    """API methods for subscription link endpoints (/sub/...)"""

    @staticmethod
    async def get_subscription(uuid: str):
        return await RemnaAPI.get(f"sub/{uuid}")

    @staticmethod
    async def get_subscription_info(uuid: str):
        return await RemnaAPI.get(f"sub/{uuid}/info")

    @staticmethod
    async def get_subscription_with_param(uuid: str, param: str):
        return await RemnaAPI.get(f"sub/{uuid}/{param}")

    @staticmethod
    async def get_outline(uuid: str, param1: str, param2: str):
        return await RemnaAPI.get(f"sub/outline/{uuid}/{param1}/{param2}")
