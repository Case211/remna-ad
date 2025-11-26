from modules.api.client import RemnaAPI
from typing import List, Dict, Any, Optional


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
    async def get_profile_by_uuid(profile_uuid: str) -> Optional[Dict[str, Any]]:
        """Get a config profile by UUID (v2.2.6)."""
        return await RemnaAPI.get(f"config-profiles/{profile_uuid}")

    @staticmethod
    async def get_computed_config(profile_uuid: str) -> Optional[Dict[str, Any]]:
        """Get computed config for a config profile (v2.2.6)."""
        return await RemnaAPI.get(f"config-profiles/{profile_uuid}/computed-config")

    @staticmethod
    async def get_profile_users(profile_uuid: str) -> List[Dict[str, Any]]:
        """Get users for a specific config profile (if supported by API)."""
        result = await RemnaAPI.get(f"config-profiles/{profile_uuid}/users")
        # Expected { response: { total, users: [...] } } or direct { users: [...] }
        if isinstance(result, dict):
            if "users" in result:
                return result.get("users") or []
            resp = result.get("response")
            if isinstance(resp, dict) and "users" in resp:
                return resp.get("users") or []
            return []
        if isinstance(result, list):
            return result
        return []


