from modules.api.client import RemnaAPI


class RemnawaveSettingsAPI:
    """API for Remnawave settings (v2.2.6)."""

    @staticmethod
    async def get_settings():
        """Get Remnawave settings."""
        return await RemnaAPI.get("remnawave-settings")

    @staticmethod
    async def update_settings(payload):
        """Update Remnawave settings."""
        return await RemnaAPI.patch("remnawave-settings", payload)

