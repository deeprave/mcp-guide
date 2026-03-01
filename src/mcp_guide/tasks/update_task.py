"""McpUpdateTask - prompts for documentation updates at startup."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import aiofiles
from anyio import Path as AsyncPath

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_init
from mcp_guide.feature_flags.constants import FLAG_AUTOUPDATE
from mcp_guide.task_manager.interception import EventType
from mcp_guide.task_manager.manager import EventResult, get_task_manager

if TYPE_CHECKING:
    from mcp_guide.task_manager.manager import TaskManager

logger = get_logger(__name__)


@task_init
class McpUpdateTask:
    """Check for documentation updates at startup and prompt if needed."""

    def __init__(self, task_manager: Optional["TaskManager"] = None) -> None:
        """Initialize McpUpdateTask.

        Args:
            task_manager: TaskManager instance (optional, uses singleton if not provided)
        """
        if task_manager is None:
            task_manager = get_task_manager()
        self.task_manager = task_manager
        self._checked = False
        self._instruction_id: Optional[str] = None

        # Subscribe to keep task alive (no specific events needed, use 0)
        self.task_manager.subscribe(self, EventType(0))

    def get_name(self) -> str:
        """Get task name.

        Returns:
            Task name
        """
        return "McpUpdateTask"

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult | None:
        """Handle task manager events (no-op for this task).

        Args:
            event_type: Type of event
            data: Event data

        Returns:
            None (event not handled)
        """
        return None

    async def on_init(self) -> None:
        """Initialize task at server startup - check for updates."""
        # Check if autoupdate flag is enabled
        if not self.task_manager.requires_flag(FLAG_AUTOUPDATE):
            logger.debug(f"McpUpdateTask disabled - {FLAG_AUTOUPDATE} flag not set")
            return

        # Get current project
        from mcp_guide.session import get_or_create_session

        try:
            session = await get_or_create_session()
        except (ValueError, AttributeError):
            logger.debug("No session available for update check")
            return

        # Check if update is needed
        docroot = Path(await session.get_docroot())
        if not await AsyncPath(docroot).exists():
            return

        version_file = docroot / ".version"
        if not await AsyncPath(version_file).exists():
            # No version file - prompt for update
            await self._prompt_update()
            return

        # Read current version
        async with aiofiles.open(version_file, "r", encoding="utf-8") as f:
            current_version = (await f.read()).strip()

        # Compare with package version
        from mcp_guide import __version__

        if current_version != __version__:
            await self._prompt_update()

    async def on_tool(self) -> None:
        """Called after tool execution - no-op."""
        pass

    async def _prompt_update(self) -> None:
        """Queue update prompt instruction."""
        from mcp_guide.render.context import TemplateContext
        from mcp_guide.render.rendering import render_content

        # Render update prompt template
        context = TemplateContext()
        rendered = await render_content("_update", "", context)

        if rendered:
            self._instruction_id = await self.task_manager.queue_instruction_with_ack(rendered.content)
            logger.info("Queued documentation update prompt")
