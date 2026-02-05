"""Client context task implementation."""

from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.context.rendering import render_context_template
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_init
from mcp_guide.feature_flags.constants import FLAG_ALLOW_CLIENT_INFO
from mcp_guide.task_manager import EventType, get_task_manager

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

        # Instruction tracking IDs
        self._os_instruction_id: Optional[str] = None
        self._context_instruction_id: Optional[str] = None

        # Subscribe to file content events
        self.task_manager.subscribe(self, EventType.FS_FILE_CONTENT)

    def get_name(self) -> str:
        """Get a readable name for the task."""
        return "ClientContextTask"

    async def on_tool(self) -> None:
        """Called after tool/prompt execution.

        Flag checking is now handled in on_init() at server startup.
        """
        pass

    async def on_init(self) -> None:
        """Initialize task at server startup.

        Checks if client info collection is enabled and requests OS info if so.
        """
        if not self.task_manager.requires_flag(FLAG_ALLOW_CLIENT_INFO):
            await self.task_manager.unsubscribe(self)
            logger.debug(f"ClientContextTask disabled - {FLAG_ALLOW_CLIENT_INFO} flag not set")
            self._flag_checked = True
            return

        if not self._os_info_requested:
            await self.request_basic_os_info()
            self._os_info_requested = True
        self._flag_checked = True

    async def request_basic_os_info(self) -> None:
        """Request basic OS information from client."""
        rendered = await render_context_template("client-context-setup")
        if rendered:
            self._os_instruction_id = await self.task_manager.queue_instruction_with_ack(rendered.content)

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> bool:
        """Handle task manager events."""
        import json
        from pathlib import Path

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

                    # Acknowledge OS info instruction
                    if self._os_instruction_id:
                        await self.task_manager.acknowledge_instruction(self._os_instruction_id)
                        self._os_instruction_id = None

                    # Invalidate template context cache
                    from mcp_guide.render.cache import invalidate_template_contexts

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

                    # Acknowledge context instruction
                    if self._context_instruction_id:
                        await self.task_manager.acknowledge_instruction(self._context_instruction_id)
                        self._context_instruction_id = None

                    # Invalidate template context cache
                    from mcp_guide.render.cache import invalidate_template_contexts

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
        rendered = await render_context_template("client-context-detailed", {"client": client_data})
        if rendered:
            self._context_instruction_id = await self.task_manager.queue_instruction_with_ack(rendered.content)
