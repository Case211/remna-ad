import asyncio
from typing import Dict, Optional
from .client import SSHSession


class SshSessionStore:
    def __init__(self):
        self._sessions: Dict[int, SSHSession] = {}
        self._locks: Dict[int, asyncio.Lock] = {}

    def _get_lock(self, chat_id: int) -> asyncio.Lock:
        if chat_id not in self._locks:
            self._locks[chat_id] = asyncio.Lock()
        return self._locks[chat_id]

    async def put(self, chat_id: int, session: SSHSession):
        async with self._get_lock(chat_id):
            old = self._sessions.pop(chat_id, None)
            if old:
                await old.close()
            self._sessions[chat_id] = session

    async def get(self, chat_id: int) -> Optional[SSHSession]:
        async with self._get_lock(chat_id):
            return self._sessions.get(chat_id)

    async def close(self, chat_id: int):
        async with self._get_lock(chat_id):
            sess = self._sessions.pop(chat_id, None)
            if sess:
                await sess.close()


SSH_SESSIONS = SshSessionStore()

