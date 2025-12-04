import logging
from typing import Any, Dict, Optional
from modules.api.client import RemnaAPI

logger = logging.getLogger(__name__)


class SnippetAPI:
    """API methods for snippets (API v2.2.6)"""

    @staticmethod
    async def get_snippets(params: Optional[Dict[str, Any]] = None):
        return await RemnaAPI.get("snippets", params=params or {})
