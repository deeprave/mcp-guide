"""Client context task implementation."""

from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_init
from mcp_guide.task_manager import EventType, get_task_manager
from mcp_guide.workflow.rendering import render_common_template

if TYPE_CHECKING:
    from mcp_guide.task_manager import TaskManager

logger = get_logger(__name__)


@task_init
class ClientContextTask:
    """Task for collecting client context information."""

    def __init__(self, task_manager: Optional["TaskManager"] = None):
        if task_manager is None:
            task_manager = get_task_manager()
        self.task_manager = task_manager
        self._os_info_requested = False
        self._flag_checked = False

        # Always subscribe - flag check happens in on_tool()
        self.task_manager.subscribe(self, EventType.TIMER_ONCE | EventType.FS_FILE_CONTENT, 0.1)

    def get_name(self) -> str:
        """Get a readable name for the task."""
        return "ClientContextTask"

    async def on_tool(self) -> None:
        """Check flag and unsubscribe if disabled."""
        if self._flag_checked:
            return

        self._flag_checked = True

        # Check if allow-client-info flag is enabled
        try:
            from mcp_guide.session import get_or_create_session

            session = await get_or_create_session()
            flags = await session.feature_flags().list()
            enabled = flags.get("allow-client-info", False) is True

            if not enabled:
                # Unsubscribe if flag is not set
                await self.task_manager.unsubscribe(self)
                logger.debug("ClientContextTask disabled - allow-client-info flag not set")
        except Exception as e:
            logger.warning(f"Failed to check allow-client-info flag, unsubscribing: {e}")
            await self.task_manager.unsubscribe(self)

    async def request_basic_os_info(self) -> None:
        """Request basic OS information from client."""
        content = await render_common_template("client-context-setup")
        await self.task_manager.queue_instruction(content)

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> bool:
        """Handle task manager events."""
        import json
        from pathlib import Path

        # Handle TIMER_ONCE startup
        if event_type & EventType.TIMER_ONCE:
            if not self._os_info_requested:
                await self.request_basic_os_info()
                self._os_info_requested = True
            return True  # Stop TIMER_ONCE

        # Handle file content events
        if event_type & EventType.FS_FILE_CONTENT:
            path = data.get("path")
            if not isinstance(path, str):
                logger.debug(f"FS_FILE_CONTENT event missing path: {data}")
                return False

            path_name = Path(path).name
            logger.debug(f"FS_FILE_CONTENT event for file: {path_name}")

            # Handle OS info response
            if path_name == ".client-os.json":
                content = data.get("content", "")
                try:
                    os_info = json.loads(content)
                    self.task_manager.set_cached_data("client_os_info", os_info)
                    # Invalidate template context cache
                    from mcp_guide.utils.template_context_cache import invalidate_template_contexts

                    invalidate_template_contexts()
                    await self._request_detailed_context(os_info)
                    return True
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse OS info JSON: {content}")
                    return False

            # Handle detailed context response
            elif path_name == ".client-context.json":
                content = data.get("content", "")
                try:
                    context_info = json.loads(content)
                    self.task_manager.set_cached_data("client_context_info", context_info)
                    # Invalidate template context cache
                    from mcp_guide.utils.template_context_cache import invalidate_template_contexts

                    invalidate_template_contexts()
                    logger.info(f"Client context received: {len(context_info)} namespaces")
                    return True
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse context info JSON: {content}")
                    return False

        return False

    async def _request_detailed_context(self, os_info: dict[str, Any]) -> None:
        """Request detailed context based on OS info."""
        client_data = os_info.get("client", {})
        content = await render_common_template("client-context-detailed", {"client": client_data})
        await self.task_manager.queue_instruction(content)
