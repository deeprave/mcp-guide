"""One-shot stdio verification of shared client filesystem access."""

import asyncio
import secrets
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_register
from mcp_guide.lazy_path import LazyPath
from mcp_guide.task_manager import EventType
from mcp_guide.task_manager.manager import EventResult

if TYPE_CHECKING:
    from mcp_guide.session import Session
    from mcp_guide.task_manager import TaskManager

logger = get_logger(__name__)
PROBE_TIMEOUT_SECONDS = 60.0


@task_register
class FilesystemProbeTask:
    """Verify one stdio filesystem, then remove all owned probe resources."""

    _pending: ClassVar[bool] = False

    def __init__(self, task_manager: "TaskManager") -> None:
        self.task_manager = task_manager
        self._session: Session | None = None
        self._path: Path | None = None
        self._challenge = ""
        self._instruction_id: str | None = None
        self._timeout_task: asyncio.Task[None] | None = None
        self._started = False
        self._finished = False

    def get_name(self) -> str:
        return "FilesystemProbeTask"

    async def start(self, task_manager: "TaskManager", session: "Session") -> bool:
        if self._started:
            return not self._finished
        if LazyPath.client_filesystem_shared is not None or type(self)._pending or session.bound_root_path is None:
            return False
        type(self)._pending = True
        self._started = True
        self.task_manager = task_manager
        self._session = session
        self._challenge = secrets.token_hex(32)
        path = session.bound_root_path / f".mcp-guide-fs-probe-{secrets.token_hex(16)}"
        try:
            # Exclusive creation and the small write form one non-awaiting ownership step.
            with path.open("x", encoding="utf-8") as stream:
                self._path = path
                stream.write(self._challenge)
            task_manager.subscribe(self, EventType.FS_FILE_CONTENT, priority=True)
            self._instruction_id = await task_manager.queue_instruction_with_ack(
                f"Read the existing file {str(path)!r} using the client's filesystem and send its exact contents "
                "through send_file_content with that exact absolute path. Do not create or modify the file. "
                "If it cannot be read, send content='unreadable' for that path. "
                "This one-time check determines whether client path shorthand is available.",
                max_retries=0,
                on_dispatch=self._on_dispatch,
            )
        except (OSError, ValueError) as error:
            logger.debug(f"Shared filesystem probe unavailable: {error}")
            await self._finish(False)
            return False
        except asyncio.CancelledError:
            await self._finish(False)
            raise
        return True

    async def _on_dispatch(self) -> None:
        if not self._finished and self._timeout_task is None:
            self._timeout_task = asyncio.create_task(self._wait_for_response())

    async def _wait_for_response(self) -> None:
        await asyncio.sleep(PROBE_TIMEOUT_SECONDS)
        if self._session is not None:
            async with self._session.work():
                await self._finish(False)

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult | None:
        if self._finished or self._path is None or not event_type & EventType.FS_FILE_CONTENT:
            return None
        if data.get("path") != str(self._path):
            return None
        shared = data.get("content") == self._challenge
        await self._finish(shared)
        return EventResult(
            result=True,
            message="Client filesystem sharing verified" if shared else "Client filesystem sharing not verified",
            consumed=True,
        )

    async def _finish(self, shared: bool) -> None:
        if not self._started or self._finished:
            return
        self._finished = True
        LazyPath.client_filesystem_shared = shared
        type(self)._pending = False
        if self._timeout_task is not None and self._timeout_task is not asyncio.current_task():
            self._timeout_task.cancel()
            try:
                await self._timeout_task
            except asyncio.CancelledError:
                pass
        if self._path is not None:
            try:
                self._path.unlink(missing_ok=True)
            except OSError as error:
                logger.warning(f"Unable to remove shared filesystem probe: {error}")
        if self._instruction_id is not None:
            await self.task_manager.acknowledge_instruction(self._instruction_id)
        await self.task_manager.unsubscribe(self)

    async def stop(self, task_manager: "TaskManager") -> None:
        await self._finish(False)

    async def on_tool(self) -> None:
        pass
