"""Workflow-specific task implementations."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from mcp_core.mcp_log import get_logger
from mcp_guide.decorators import task_init
from mcp_guide.models import FileReadError, NoProjectError
from mcp_guide.task_manager import EventType, get_task_manager
from mcp_guide.workflow.change_detection import ChangeEvent, detect_workflow_changes
from mcp_guide.workflow.instruction_generator import get_instruction_template_for_change
from mcp_guide.workflow.parser import parse_workflow_state
from mcp_guide.workflow.rendering import render_workflow_template

if TYPE_CHECKING:
    from mcp_guide.task_manager import TaskManager

logger = get_logger(__name__)

# Workflow monitoring interval in seconds
WORKFLOW_INTERVAL = 120.0


@task_init
class WorkflowMonitorTask:
    """Scheduled background monitoring task for workflow state changes."""

    # noinspection PyMethodMayBeStatic
    def get_name(self) -> str:
        """Get a readable name for the task."""
        return "WorkflowMonitorTask"

    def __init__(
        self,
        workflow_file_path: Optional[str] = None,
    ):
        # Use default workflow file if none provided
        if workflow_file_path is None:
            from mcp_guide.workflow.constants import DEFAULT_WORKFLOW_FILE

            workflow_file_path = str(DEFAULT_WORKFLOW_FILE)

        self.workflow_file_path = workflow_file_path

        # Get the singleton TaskManager
        self.task_manager: "TaskManager" = get_task_manager()

        self._cached_content: Optional[str] = None
        self._cached_mtime: Optional[float] = None
        self._setup_done = False

        # Subscribe self to task manager
        self.task_manager.subscribe(self, EventType.TIMER | EventType.FS_FILE_CONTENT, WORKFLOW_INTERVAL)

    async def on_tool(self) -> None:
        """Called after tool/prompt execution."""
        logger.trace(f"WorkflowMonitorTask.on_tool called, _setup_done={self._setup_done}")
        if not self._setup_done:
            try:
                content = await render_workflow_template("monitoring-setup")
                await self.task_manager.queue_instruction(content)
                self._setup_done = True
                logger.trace("WorkflowMonitorTask.on_tool: Queued setup instruction")
            except Exception as e:
                logger.warning(f"Failed to queue workflow setup: {e}")

    async def handle_event(self, event_type: "EventType", data: dict[str, Any]) -> bool:
        """Handle task manager events."""
        logger.trace(f"WorkflowMonitorTask received event: {event_type} for path: {data.get('path', 'unknown')}")

        # Handle timer events for monitoring reminders
        if event_type & EventType.TIMER:
            await self._handle_monitoring_reminder()
            return True

        # Check if the file content is for our workflow file (compare basenames)
        path = data.get("path")
        if isinstance(path, str) and Path(path).name == Path(self.workflow_file_path).name:
            # Process the data
            await self._process_workflow_content(data.get("content", ""))
            return True
        return False

    async def _handle_monitoring_reminder(self) -> None:
        """Handle timer events for monitoring reminders."""
        try:
            content = await render_workflow_template("monitoring-reminder")
            await self.task_manager.queue_instruction(content)
        except (NoProjectError, FileReadError) as e:
            logger.warning(f"Monitoring reminder failed due to configuration issue: {e}")
        except Exception as e:
            logger.error(f"Failed to queue monitoring reminder: {e}", exc_info=True)

    async def _process_workflow_content(self, content: str) -> None:
        """Process workflow file content and update cached state."""
        logger.trace("_process_workflow_content called")
        try:
            new_state = parse_workflow_state(content)
            if not new_state:
                logger.warning("Failed to parse workflow state - not processing changes")
                return

            logger.trace(f"Parsed new workflow state: phase={new_state.phase}, issue={new_state.issue}")

            # Get previous state from cache for comparison
            old_state = self.task_manager.get_cached_data("workflow_state")
            logger.trace(f"Retrieved old state from cache: {old_state is not None}")

            # Detect semantic changes
            changes = detect_workflow_changes(old_state, new_state)
            logger.trace(f"Detected {len(changes)} workflow changes")

            # Process each detected change and get rendered content for main response
            if changes:
                change_content = await self._process_workflow_changes(changes)
                if change_content:
                    # Store the change content to be used as the main response value
                    self.task_manager.set_cached_data("workflow_change_content", change_content)

            # Always queue monitoring instruction after successful parse (maintains original behaviour)
            # This ensures the critical "MUST send file content" instruction is always provided
            try:
                content = await render_workflow_template("monitoring-result")
                await self.task_manager.queue_instruction(content)
            except (NoProjectError, FileReadError) as e:
                logger.warning(f"Monitoring result failed due to configuration issue: {e}")
            except Exception as e:
                logger.error(f"Failed to queue monitoring result instruction: {e}", exc_info=True)

            # Update cache with new state AFTER processing changes
            self.task_manager.set_cached_data("workflow_state", new_state)
            logger.trace("New workflow state cached in TaskManager")

        except Exception as e:
            logger.error(f"Failed to process workflow content: {e}", exc_info=True)

    @staticmethod
    async def _process_workflow_changes(changes: list[ChangeEvent]) -> Optional[str]:
        """Process detected workflow changes and return rendered content for main response.

        Returns:
            Rendered change content for main response, or None if no content to return
        """
        # Process each change using existing workflow instruction system
        rendered_contents = []
        for change in changes:
            logger.trace(f"Processing change: {change.change_type.value}")

            # Get appropriate template pattern for this change
            template_pattern = get_instruction_template_for_change(change)

            # Render template content for main response
            try:
                content = await render_workflow_template(template_pattern)
                rendered_contents.append(content)
                logger.trace(
                    f"Rendered workflow content for {change.change_type.value} using pattern: {template_pattern}"
                )
            except (NoProjectError, FileReadError) as e:
                logger.warning(f"Template rendering failed for {template_pattern}: {e}")
            except Exception as e:
                logger.error(f"Failed to render template {template_pattern}: {e}", exc_info=True)

        # Combine all rendered content
        return "\n".join(rendered_contents) if rendered_contents else None
