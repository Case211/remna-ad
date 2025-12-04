import logging
from modules.api.client import RemnaAPI
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigProfileAPI:
    """API methods for config profiles (v208)"""

    @staticmethod
    async def get_profiles() -> List[Dict[str, Any]]:
        """Get all config profiles"""
        result = await RemnaAPI.get("config-profiles")
        # v208 returns { response: { total, configProfiles: [...] } }
        if isinstance(result, dict):
            # If RemnaAPI already unwrapped 'response', we have { total, configProfiles }
            if "configProfiles" in result:
                return result.get("configProfiles") or []
            # If response not unwrapped (unlikely), try deeper
            resp = result.get("response")
            if isinstance(resp, dict) and "configProfiles" in resp:
                return resp.get("configProfiles") or []
            # Fallbacks
            return []
        # Unexpected — return empty list
        return []

    @staticmethod
    async def get_profile_inbounds(profile_uuid: str) -> List[Dict[str, Any]]:
        """Get inbounds for a specific config profile"""
        result = await RemnaAPI.get(f"config-profiles/{profile_uuid}/inbounds")
        # v208 returns { response: { total, inbounds: [...] } }
        if isinstance(result, dict):
            if "inbounds" in result:
                return result.get("inbounds") or []
            resp = result.get("response")
            if isinstance(resp, dict) and "inbounds" in resp:
                return resp.get("inbounds") or []
            return []
        return []

    @staticmethod
    async def get_profile_users(profile_uuid: str) -> List[Dict[str, Any]]:
        """Deprecated in API v2.2.6: endpoint removed, keep shim to avoid 404."""
        logger.info("config-profiles/{uuid}/users is not available in API v2.2.6; returning empty list")
        return []


