"""Client context task implementation."""

from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.context.rendering import render_context_template
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_register
from mcp_guide.feature_flags.constants import FLAG_ALLOW_CLIENT_INFO
from mcp_guide.task_manager import EventType
from mcp_guide.task_manager.protocol import DEFAULT_ONCE_INTERVAL, InitialisableMixin

if TYPE_CHECKING:
    from mcp_guide.task_manager.activation import TaskActivation
    from mcp_guide.task_manager.manager import EventResult

logger = get_logger(__name__)


@task_register
class ClientContextTask(InitialisableMixin):
    """Task for collecting client context information."""

    configuration_flags = frozenset({FLAG_ALLOW_CLIENT_INFO})

    def __init__(self) -> None:
        """Create an inactive client-context task."""
        self.activation: TaskActivation | None = None
        self._session: Any = None
        self._os_info_requested = False
        self._flag_checked = False

        # Instruction tracking IDs
        self._os_instruction_id: Optional[str] = None
        self._context_instruction_id: Optional[str] = None
        self._started = False

    def get_name(self) -> str:
        """Get a readable name for the task."""
        return "ClientContextTask"

    async def start(self, activation: "TaskActivation") -> bool:
        """Start client context collection if enabled for the current project."""
        if self._started:
            return True

        self.activation = activation
        self._session = activation.session
        if not await activation.requires_flag(FLAG_ALLOW_CLIENT_INFO):
            logger.debug(f"ClientContextTask disabled - {FLAG_ALLOW_CLIENT_INFO} flag not set")
            self._flag_checked = True
            return False

        activation.subscribe(EventType.FS_FILE_CONTENT, once_interval=DEFAULT_ONCE_INTERVAL)
        self._started = True
        return True

    async def stop(self) -> None:
        """Reset startup state when the task is stopped."""
        self._started = False

    async def on_tool(self) -> None:
        pass

    async def _initialise(self) -> "EventResult":
        """Check flag and request OS info if enabled."""
        from mcp_guide.task_manager.manager import EventResult

        if self._session is None:
            return EventResult(result=False, message="Client context task is not attached to a Session")
        if self.activation is None:
            return EventResult(result=False, message="Client context task has no activation")
        allow_client_info = await self.activation.requires_flag(FLAG_ALLOW_CLIENT_INFO)

        if not allow_client_info:
            await self.activation.unsubscribe()
            self._started = False
            logger.debug(f"ClientContextTask disabled - {FLAG_ALLOW_CLIENT_INFO} flag not set")
            self._flag_checked = True
            return EventResult(result=True)

        if not self._os_info_requested:
            await self.request_basic_os_info()
            self._os_info_requested = True
        self._flag_checked = True
        return EventResult(result=True)

    async def request_basic_os_info(self) -> None:
        """Request basic OS information from client."""
        rendered = await render_context_template(self._session, "client-context-setup")
        if rendered:
            if self.activation is not None:
                self._os_instruction_id = await self.activation.queue_instruction_with_ack(rendered.content)

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> "EventResult | None":
        """Handle task manager events."""
        import json
        from pathlib import Path

        from mcp_guide.task_manager.manager import EventResult

        if result := await self._handle_timer_once(event_type):
            return result

        # Handle file content events
        if event_type & EventType.FS_FILE_CONTENT:
            path = data.get("path")
            if not isinstance(path, str):
                logger.debug(f"FS_FILE_CONTENT event missing path: {data}")
                return None

            path_name = Path(path).name
            logger.debug(f"FS_FILE_CONTENT event for file: {path_name}")

            # Handle OS info response
            if path_name == ".client-os.json":
                content = data.get("content", "")
                try:
                    os_info = json.loads(content)
                    if self.activation is None:
                        return None
                    self.activation.set_cached_data("client_os_info", os_info)

                    # Acknowledge OS info instruction
                    if self._os_instruction_id:
                        await self.activation.acknowledge_instruction(self._os_instruction_id)
                        self._os_instruction_id = None

                    # Invalidate template context cache
                    from mcp_guide.render.cache import invalidate_template_contexts

                    invalidate_template_contexts(self._session)
                    await self._request_detailed_context(os_info)
                    return EventResult(result=True)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse OS info JSON: {content}")
                    return None

            # Handle detailed context response
            elif path_name == ".client-context.json":
                content = data.get("content", "")
                try:
                    context_info = json.loads(content)
                    if self.activation is None:
                        return None
                    self.activation.set_cached_data("client_context_info", context_info)

                    # Acknowledge context instruction
                    if self._context_instruction_id:
                        await self.activation.acknowledge_instruction(self._context_instruction_id)
                        self._context_instruction_id = None

                    # Invalidate template context cache
                    from mcp_guide.render.cache import invalidate_template_contexts

                    invalidate_template_contexts(self._session)
                    logger.info(f"Client context received: {len(context_info)} namespaces")
                    return EventResult(result=True)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse context info JSON: {content}")
                    return None

        return None

    async def _request_detailed_context(self, os_info: dict[str, Any]) -> None:
        """Request detailed context based on OS info."""
        client_data = os_info.get("client", {})
        rendered = await render_context_template(self._session, "client-context-detailed", {"client": client_data})
        if rendered:
            if self.activation is not None:
                self._context_instruction_id = await self.activation.queue_instruction_with_ack(rendered.content)
