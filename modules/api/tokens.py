import logging
from typing import Any, Dict, Optional
from modules.api.client import RemnaAPI

logger = logging.getLogger(__name__)


class TokenAPI:
    """API methods for token management (API v2.2.6)"""

    @staticmethod
    async def list_tokens(params: Optional[Dict[str, Any]] = None):
        return await RemnaAPI.get("tokens", params=params or {})

    @staticmethod
    async def get_token(uuid: str):
        return await RemnaAPI.get(f"tokens/{uuid}")
