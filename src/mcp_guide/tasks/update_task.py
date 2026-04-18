"""McpUpdateTask - prompts for documentation updates at startup."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from anyio import Path as AsyncPath

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_init
from mcp_guide.feature_flags.constants import FLAG_AUTOUPDATE
from mcp_guide.installer.core import DocrootValidationError, read_version, validate_docroot_safety
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
        self._instruction_id: Optional[str] = None

        # Subscribe to one-shot timer with 1-second delay to check for updates after startup
        self.task_manager.subscribe(self, EventType.TIMER_ONCE, once_interval=1.0)

    def get_name(self) -> str:
        """Get task name.

        Returns:
            Task name
        """
        return "McpUpdateTask"

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult | None:
        """Handle timer event to check for updates.

        Args:
            event_type: Type of event
            data: Event data

        Returns:
            EventResult with result status, or None if not handled
        """
        from mcp_guide.task_manager.manager import EventResult

        # Only handle timer events
        if not (event_type & EventType.TIMER_ONCE):
            return None

        try:
            # Autoupdate is opt-out: only explicit false disables startup prompting.
            autoupdate = (await self.task_manager.resolved_flags()).get(FLAG_AUTOUPDATE)
            if autoupdate is False:
                logger.debug("McpUpdateTask disabled - autoupdate explicitly set to false")
                return EventResult(result=True)

            # Get current project
            from mcp_guide.session import get_session

            try:
                session = await get_session()
            except (ValueError, AttributeError):
                logger.debug("No session available for update check")
                return EventResult(result=True)

            # Check if update is needed
            docroot = Path(await session.get_docroot())
            if not await AsyncPath(docroot).exists():
                return EventResult(result=True)

            try:
                await validate_docroot_safety(docroot)
            except DocrootValidationError:
                logger.debug("Docroot %s is not updatable; skipping update prompt", docroot)
                return EventResult(result=True)
            except FileNotFoundError as exc:
                logger.warning(
                    "Unable to validate docroot %s; skipping update prompt: %s",
                    docroot,
                    exc,
                )
                return EventResult(result=True)

            # Read current version with error handling
            try:
                current_version = await read_version(docroot)
            except (OSError, IOError) as exc:
                logger.warning(
                    "Failed to read version file in %s; skipping update check: %s",
                    docroot,
                    exc,
                )
                return EventResult(result=True)

            # Missing version marker means there is no valid installed-docs state to update.
            if current_version is None:
                return EventResult(result=True)

            # Compare with package version
            from mcp_guide import __version__

            if current_version != __version__:
                await self._prompt_update()

            return EventResult(result=True)
        finally:
            # Unsubscribe after handling one-shot timer
            await self.task_manager.unsubscribe(self)

    async def on_tool(self) -> None:
        """Called after tool execution - no-op."""
        pass

    async def acknowledge_update(self) -> None:
        """Acknowledge the update instruction to prevent retry loop."""
        if self._instruction_id:
            await self.task_manager.acknowledge_instruction(self._instruction_id)
            self._instruction_id = None

    async def _prompt_update(self) -> None:
        """Queue update prompt instruction."""
        from mcp_guide.render.context import TemplateContext
        from mcp_guide.render.rendering import render_content

        # Render update prompt template
        context = TemplateContext()
        rendered = await render_content("_update", "_system", context)

        if rendered:
            self._instruction_id = await self.task_manager.queue_instruction_with_ack(rendered.content)
            logger.info("Queued documentation update prompt")
