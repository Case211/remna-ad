import logging
from typing import Any, Dict, Optional
from modules.api.client import RemnaAPI

logger = logging.getLogger(__name__)


class InfraBillingAPI:
    """API methods for infra-billing endpoints (API v2.2.6)"""

    @staticmethod
    async def get_history(params: Optional[Dict[str, Any]] = None):
        return await RemnaAPI.get("infra-billing/history", params=params or {})

    @staticmethod
    async def get_history_item(uuid: str):
        return await RemnaAPI.get(f"infra-billing/history/{uuid}")

    @staticmethod
    async def get_nodes(params: Optional[Dict[str, Any]] = None):
        return await RemnaAPI.get("infra-billing/nodes", params=params or {})

    @staticmethod
    async def get_node(uuid: str):
        return await RemnaAPI.get(f"infra-billing/nodes/{uuid}")

    @staticmethod
    async def get_providers(params: Optional[Dict[str, Any]] = None):
        return await RemnaAPI.get("infra-billing/providers", params=params or {})

    @staticmethod
    async def get_provider(uuid: str):
        return await RemnaAPI.get(f"infra-billing/providers/{uuid}")
