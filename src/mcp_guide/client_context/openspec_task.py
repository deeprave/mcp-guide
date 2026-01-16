"""OpenSpec CLI detection task."""

from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_init
from mcp_guide.feature_flags.constants import FLAG_OPENSPEC
from mcp_guide.task_manager import EventType, get_task_manager
from mcp_guide.workflow.rendering import render_common_template

if TYPE_CHECKING:
    from mcp_guide.task_manager import TaskManager

logger = get_logger(__name__)


@task_init
class OpenSpecTask:
    """Task for detecting OpenSpec CLI availability."""

    def __init__(self, task_manager: Optional["TaskManager"] = None):
        if task_manager is None:
            task_manager = get_task_manager()
        self.task_manager = task_manager
        self._cli_requested = False
        self._flag_checked = False
        self._available: Optional[bool] = None

        # Subscribe to startup and command events
        self.task_manager.subscribe(self, EventType.TIMER_ONCE | EventType.FS_COMMAND, 5.0)

    def get_name(self) -> str:
        """Get a readable name for the task."""
        return "OpenSpecTask"

    async def on_tool(self) -> None:
        """Check flag and unsubscribe if disabled."""
        if self._flag_checked:
            return

        self._flag_checked = True

        try:
            from mcp_guide.session import get_or_create_session
            from mcp_guide.utils.flag_utils import get_resolved_flag_value

            session = await get_or_create_session()
            enabled = await get_resolved_flag_value(session, FLAG_OPENSPEC, False)

            if not enabled:
                await self.task_manager.unsubscribe(self)
                logger.debug(f"OpenSpecTask disabled - {FLAG_OPENSPEC} flag not set")
        except Exception as e:
            logger.warning(f"Failed to check openspec flag, unsubscribing: {e}")
            await self.task_manager.unsubscribe(self)

    def is_available(self) -> Optional[bool]:
        """Check if OpenSpec CLI is available.

        Returns:
            True if available, False if not available, None if not yet checked.
        """
        return self._available

    async def request_cli_check(self) -> None:
        """Request OpenSpec CLI availability check from client."""
        content = await render_common_template("openspec-cli-check")
        await self.task_manager.queue_instruction(content)

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> bool:
        """Handle task manager events."""
        # Handle TIMER_ONCE startup
        if event_type & EventType.TIMER_ONCE:
            if not self._cli_requested:
                await self.request_cli_check()
                self._cli_requested = True
            return True

        # Handle command location events
        if event_type & EventType.FS_COMMAND:
            command = data.get("command")
            if command == "openspec":
                path = data.get("path", "")
                found = data.get("found", False)
                self._available = found and bool(path)
                self.task_manager.set_cached_data("openspec_available", self._available)
                logger.info(f"OpenSpec CLI {'available' if self._available else 'not available'}")
                return True

        return False
