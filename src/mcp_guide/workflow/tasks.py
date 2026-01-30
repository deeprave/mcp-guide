"""Workflow-specific task implementations."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_init
from mcp_guide.feature_flags.constants import FLAG_WORKFLOW
from mcp_guide.task_manager import EventType, get_task_manager
from mcp_guide.workflow.change_detection import ChangeEvent, detect_workflow_changes
from mcp_guide.workflow.constants import DEFAULT_WORKFLOW_FILE
from mcp_guide.workflow.instruction_generator import get_instruction_template_for_change
from mcp_guide.workflow.parser import parse_workflow_state
from mcp_guide.workflow.rendering import render_workflow_template

if TYPE_CHECKING:
    from mcp_guide.task_manager import TaskManager

logger = get_logger(__name__)

# Workflow monitoring interval in seconds
WORKFLOW_INTERVAL = 600.0  # 10 minutes


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
            workflow_file_path = str(DEFAULT_WORKFLOW_FILE)

        self.workflow_file_path = workflow_file_path

        # Get the singleton TaskManager
        self.task_manager: "TaskManager" = get_task_manager()

        self._cached_content: Optional[str] = None
        self._cached_mtime: Optional[float] = None
        self._setup_done = False

        # Subscribe self to task manager for workflow monitoring with 15s initial delay
        self.task_manager.subscribe(self, EventType.TIMER | EventType.FS_FILE_CONTENT, WORKFLOW_INTERVAL, 15.0)

    async def on_tool(self) -> None:
        """Called after tool/prompt execution.

        Flag checking and setup are now handled in on_init() at server startup.
        """
        pass

    async def on_init(self) -> None:
        """Initialize task at server startup.

        Checks if workflow is enabled and queues setup instructions if so.
        """
        if not self.task_manager.requires_flag(FLAG_WORKFLOW):
            await self.task_manager.unsubscribe(self)
            logger.debug(f"WorkflowMonitorTask disabled - {FLAG_WORKFLOW} flag not set")
            return

        # Get workflow file path from flags
        from mcp_guide.feature_flags.constants import FLAG_WORKFLOW_FILE

        workflow_file = (
            self.task_manager.resolved_flags.get(FLAG_WORKFLOW_FILE) if self.task_manager.resolved_flags else None
        )
        if workflow_file and isinstance(workflow_file, str):
            self.workflow_file_path = workflow_file
            # Cache the workflow file path for template context
            self.task_manager.set_cached_data("workflow_file_path", workflow_file)
            logger.debug(f"WorkflowMonitorTask using workflow file from flag: {workflow_file}")

        if not self._setup_done:
            content = await render_workflow_template("monitoring-setup")
            if content:
                await self.task_manager.queue_instruction(content)
            self._setup_done = True
            logger.debug("WorkflowMonitorTask initialized")

    async def handle_event(self, event_type: "EventType", data: dict[str, Any]) -> bool:
        """Handle task manager events."""
        logger.trace(f"WorkflowMonitorTask received event: {event_type} for path: {data.get('path', 'unknown')}")

        # Handle timer events
        if event_type & EventType.TIMER:
            interval = data.get("interval")

            # Workflow monitoring reminder (10 min interval)
            if interval == WORKFLOW_INTERVAL:
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
        """Handle timer events for workflow monitoring reminders."""
        content = await render_workflow_template("monitoring-reminder")
        if content:
            await self.task_manager.queue_instruction(content)

    async def _process_workflow_content(self, content: str) -> None:
        """Process workflow file content and update cached state."""
        logger.trace("_process_workflow_content called")
        try:
            new_state = parse_workflow_state(content)
            if not new_state:
                logger.warning("Failed to parse workflow state - not processing changes")
                return

            logger.trace(
                f"WorkflowMonitorTask: Parsed workflow state - phase={new_state.phase}, issue={new_state.issue}"
            )

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

            # Always queue monitoring instruction after successful parse
            result_content = await render_workflow_template("monitoring-result")
            if result_content:
                await self.task_manager.queue_instruction(result_content)

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
            content = await render_workflow_template(template_pattern)
            if content:
                rendered_contents.append(content)
            logger.trace(f"Rendered workflow content for {change.change_type.value} using pattern: {template_pattern}")

        # Combine all rendered content
        return "\n".join(rendered_contents) if rendered_contents else None
