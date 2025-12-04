import logging
from typing import Any, Dict, List, Optional
from modules.api.client import RemnaAPI

logger = logging.getLogger(__name__)


class SquadAPI:
    """API methods for internal and external squads (API v2.2.6)"""

    @staticmethod
    async def get_internal_squads(params: Optional[Dict[str, Any]] = None):
        """Fetch internal squads"""
        return await RemnaAPI.get("internal-squads", params=params or {})

    @staticmethod
    async def get_external_squads(params: Optional[Dict[str, Any]] = None):
        """Fetch external squads"""
        return await RemnaAPI.get("external-squads", params=params or {})

    @staticmethod
    async def add_users_to_internal_squad(squad_uuid: str, user_uuids: List[str]):
        """Add users to an internal squad"""
        payload = {"uuids": user_uuids}
        return await RemnaAPI.post(f"internal-squads/{squad_uuid}/bulk-actions/add-users", payload)

    @staticmethod
    async def add_users_to_external_squad(squad_uuid: str, user_uuids: List[str]):
        """Add users to an external squad"""
        payload = {"uuids": user_uuids}
        return await RemnaAPI.post(f"external-squads/{squad_uuid}/bulk-actions/add-users", payload)

    @staticmethod
    async def bulk_update_internal_squads(user_uuids: List[str], internal_squad_uuids: List[str]):
        """Bulk update users' internal squads"""
        payload = {
            "uuids": user_uuids,
            "activeInternalSquads": internal_squad_uuids
        }
        return await RemnaAPI.post("users/bulk/update-squads", payload)
