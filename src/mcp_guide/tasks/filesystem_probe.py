"""One-shot stdio verification of shared client filesystem access."""

import asyncio
import secrets
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from anyio import Path as AsyncPath

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_register
from mcp_guide.lazy_path import LazyPath
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.rendering import render_content
from mcp_guide.task_manager import EventType
from mcp_guide.task_manager.manager import EventResult

if TYPE_CHECKING:
    from mcp_guide.session import Session
    from mcp_guide.task_manager.activation import TaskActivation

logger = get_logger(__name__)
PROBE_TIMEOUT_SECONDS = 60.0
PROBE_BASE = Path("/tmp")  # nosec B108: required shared base for the stdio filesystem probe.


@task_register
class FilesystemProbeTask:
    """Verify one stdio filesystem, then remove all owned probe resources."""

    configuration_flags = frozenset()

    _pending: ClassVar[bool] = False

    def __init__(self) -> None:
        self.activation: TaskActivation | None = None
        self._session: Session | None = None
        self._path: Path | None = None
        self._challenge = ""
        self._instruction_id: str | None = None
        self._timeout_task: asyncio.Task[None] | None = None
        self._started = False
        self._finished = False

    def get_name(self) -> str:
        return "FilesystemProbeTask"

    async def start(self, activation: "TaskActivation") -> bool:
        if self._started:
            return not self._finished
        session = activation.session
        if LazyPath.client_filesystem_shared is not None or type(self)._pending or session.bound_root_path is None:
            return False
        type(self)._pending = True
        self._started = True
        self.activation = activation
        self._session = session
        self._challenge = secrets.token_hex(32)
        path = PROBE_BASE / f".mcp-guide-fs-probe-{secrets.token_hex(16)}"
        self._path = path
        try:
            # Exclusive creation establishes ownership before the path is announced.
            async_path = AsyncPath(path)
            async with await async_path.open("x", encoding="utf-8") as stream:
                await stream.write(self._challenge)
            await async_path.chmod(0o444)
            activation.subscribe(EventType.FS_FILE_CONTENT, priority=True)
            rendered = await render_content(
                session,
                "_filesystem-probe",
                "_system",
                TemplateContext({"path": str(path)}),
            )
            if rendered is None:
                logger.debug("Filesystem probe template did not render; abandoning probe")
                await self._finish(False)
                return False
            self._instruction_id = await activation.queue_instruction_with_ack(
                rendered.content,
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
                await AsyncPath(self._path).unlink()
            except FileNotFoundError:
                pass
            except OSError as error:
                logger.warning(f"Unable to remove shared filesystem probe: {error}")
        if self._instruction_id is not None:
            if self.activation is not None:
                await self.activation.acknowledge_instruction(self._instruction_id)
        if self.activation is not None:
            await self.activation.unsubscribe()

    async def stop(self) -> None:
        await self._finish(False)

    async def on_tool(self) -> None:
        pass
