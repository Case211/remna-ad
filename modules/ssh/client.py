import asyncio
import asyncssh
import logging
from typing import Optional


logger = logging.getLogger(__name__)


class SSHSession:
    def __init__(self, conn: asyncssh.SSHClientConnection, proc: asyncssh.SSHClientProcess):
        self._conn = conn
        self._proc = proc
        self._reader_task: Optional[asyncio.Task] = None
        self._closed = False
        # Active foreground command process & transcript
        self._active_proc: Optional[asyncssh.SSHClientProcess] = None
        self._active_reader_task: Optional[asyncio.Task] = None
        self._active_buffer: bytearray = bytearray()

    @property
    def connected(self) -> bool:
        return not self._closed and self._conn is not None and self._proc is not None

    async def start_reader(self, bot, chat_id: int, thread_id: int | None = None):
        async def _reader():
            try:
                while not self._proc.exit_status_ready():
                    chunk = await self._proc.stdout.read(4096)
                    if not chunk:
                        await asyncio.sleep(0.05)
                        continue
                    # Telegram messages limit ~4096 chars; chunk further if needed
                    while chunk:
                        part = chunk[:4000]
                        chunk = chunk[4000:]
                        try:
                            if thread_id:
                                await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text=part)
                            else:
                                await bot.send_message(chat_id=chat_id, text=part)
                        except Exception:
                            logger.debug("Failed to send SSH output chunk to Telegram", exc_info=True)
            except Exception:
                logger.debug("SSH reader loop ended", exc_info=True)

        self._reader_task = asyncio.create_task(_reader())

    async def send_line(self, line: str):
        if not self.connected:
            return
        try:
            self._proc.stdin.write(line + "\n")
            await self._proc.stdin.drain()
        except Exception:
            logger.debug("Failed to write to SSH stdin", exc_info=True)

    async def start_command(self, bot, chat_id: int, command: str, thread_id: int | None = None) -> bool:
        """Start a foreground interactive command which streams output to chat & stores transcript."""
        # Close previous foreground command if exists
        if self._active_proc:
            try:
                self._active_proc.terminate()
            except Exception:
                pass
            self._active_proc = None

        try:
            proc = await self._conn.create_process(command, term_type="xterm")
            self._active_proc = proc

            async def _reader():
                try:
                    while not proc.exit_status_ready():
                        chunk = await proc.stdout.read(4096)
                        if not chunk:
                            await asyncio.sleep(0.05)
                            continue
                        # record to buffer and stream to chat
                        try:
                            self._active_buffer.extend(chunk.encode() if isinstance(chunk, str) else chunk)
                        except Exception:
                            pass
                        text = chunk if isinstance(chunk, str) else chunk.decode(errors='ignore')
                        while text:
                            part = text[:4000]
                            text = text[4000:]
                            try:
                                if thread_id:
                                    await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text=part)
                                else:
                                    await bot.send_message(chat_id=chat_id, text=part)
                            except Exception:
                                logger.debug("Failed to send command output chunk", exc_info=True)
                except Exception:
                    logger.debug("Active command reader ended", exc_info=True)

            self._active_reader_task = asyncio.create_task(_reader())
            return True
        except Exception:
            logger.error("Failed to start command process", exc_info=True)
            return False

    async def send_to_command(self, line: str) -> bool:
        if not self._active_proc:
            return False
        try:
            self._active_proc.stdin.write(line + "\n")
            await self._active_proc.stdin.drain()
            return True
        except Exception:
            logger.debug("Failed to write to active command stdin", exc_info=True)
            return False

    async def stop_command(self):
        if not self._active_proc:
            return None
        try:
            self._active_proc.terminate()
        except Exception:
            pass
        await asyncio.sleep(0.1)
        data = bytes(self._active_buffer)
        self._active_buffer.clear()
        self._active_proc = None
        if self._active_reader_task:
            self._active_reader_task.cancel()
            self._active_reader_task = None
        return data

    def snapshot_command_output(self) -> bytes:
        """Return a snapshot of current foreground command transcript without stopping it."""
        return bytes(self._active_buffer)

    async def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            if self._proc is not None:
                try:
                    self._proc.terminate()
                except Exception:
                    pass
            if self._active_proc is not None:
                try:
                    self._active_proc.terminate()
                except Exception:
                    pass
            if self._reader_task:
                self._reader_task.cancel()
            if self._active_reader_task:
                self._active_reader_task.cancel()
        finally:
            try:
                if self._conn is not None:
                    self._conn.close()
                    await self._conn.wait_closed()
            except Exception:
                pass


async def connect_interactive(host: str, username: str, password: str, port: int = 22) -> Optional[SSHSession]:
    """Open an SSH connection and start an interactive shell with PTY."""
    try:
        conn = await asyncssh.connect(
            host=host,
            port=port,
            username=username,
            password=password,
            known_hosts=None,
            client_keys=None,
            server_host_key_algs=["ssh-rsa", "ssh-ed25519", "rsa-sha2-512", "rsa-sha2-256"],
        )

        try:
            proc = await conn.create_process(term_type="xterm")
        except Exception:
            try:
                proc = await conn.create_process("bash -l", term_type="xterm")
            except Exception:
                proc = await conn.create_process("sh -l", term_type="xterm")

        return SSHSession(conn, proc)
    except (asyncssh.PermissionDenied, asyncssh.DisconnectError) as e:
        logger.info(f"SSH auth/connection failed to {host}: {e}")
        return None
    except Exception:
        logger.error(f"SSH connection error to {host}", exc_info=True)
        return None
