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
    from mcp_guide.render.content import RenderedContent
    from mcp_guide.task_manager import TaskManager
    from mcp_guide.task_manager.manager import EventResult

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

        # Instruction tracking IDs
        self._setup_instruction_id: Optional[str] = None
        self._reminder_instruction_id: Optional[str] = None

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
            rendered = await render_workflow_template("monitoring-setup")
            if rendered:
                self._setup_instruction_id = await self.task_manager.queue_instruction_with_ack(rendered.content)
            self._setup_done = True
            logger.debug("WorkflowMonitorTask initialized")

    async def handle_event(self, event_type: "EventType", data: dict[str, Any]) -> "EventResult | None":
        """Handle task manager events."""
        from mcp_guide.task_manager.manager import EventResult

        logger.trace(f"WorkflowMonitorTask received event: {event_type} for path: {data.get('path', 'unknown')}")

        # Handle timer events
        if event_type & EventType.TIMER:
            interval = data.get("timer_interval")

            # Workflow monitoring reminder (10 min interval)
            if interval == WORKFLOW_INTERVAL:
                await self._handle_monitoring_reminder()
                return EventResult(result=True)

        # Check if the file content is for our workflow file (compare basenames)
        path = data.get("path")
        if isinstance(path, str) and Path(path).name == Path(self.workflow_file_path).name:
            # Acknowledge any pending instructions
            if self._setup_instruction_id:
                await self.task_manager.acknowledge_instruction(self._setup_instruction_id)
                self._setup_instruction_id = None
            if self._reminder_instruction_id:
                await self.task_manager.acknowledge_instruction(self._reminder_instruction_id)
                self._reminder_instruction_id = None

            # Process the data
            await self._process_workflow_content(data.get("content", ""))
            return EventResult(result=True)
        return None

    async def _handle_monitoring_reminder(self) -> None:
        """Handle timer events for workflow monitoring reminders."""
        rendered = await render_workflow_template("monitoring-reminder")
        if rendered:
            self._reminder_instruction_id = await self.task_manager.queue_instruction_with_ack(rendered.content)

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
                rendered_change = await self._process_workflow_changes(changes)
                if rendered_change:
                    # Store the rendered content to be used as the main response
                    self.task_manager.set_cached_data("workflow_change_content", rendered_change)

            # Update cache with new state AFTER processing changes
            self.task_manager.set_cached_data("workflow_state", new_state)
            logger.trace("New workflow state cached in TaskManager")

        except Exception as e:
            logger.error(f"Failed to process workflow content: {e}", exc_info=True)

    @staticmethod
    async def _process_workflow_changes(changes: list[ChangeEvent]) -> Optional["RenderedContent"]:
        """Process detected workflow changes and return rendered content for main response.

        Returns:
            RenderedContent with combined content and instructions, or None if no content to return
        """
        from mcp_guide.render.content import RenderedContent
        from mcp_guide.render.frontmatter_types import Frontmatter

        # Process each change using existing workflow instruction system
        rendered_list: list[RenderedContent] = []
        for change in changes:
            logger.trace(f"Processing change: {change.change_type.value}")

            # Get appropriate template pattern for this change
            template_pattern = get_instruction_template_for_change(change)

            # Render template content for main response
            rendered = await render_workflow_template(template_pattern)
            if rendered:
                rendered_list.append(rendered)
                logger.trace(
                    f"Rendered workflow content for {change.change_type.value} using pattern: {template_pattern}"
                )
            else:
                logger.trace(
                    f"Workflow content filtered or unavailable for {change.change_type.value} using pattern: {template_pattern}"
                )

        if not rendered_list:
            return None

        # Combine all rendered content and instructions
        combined_content = "\n".join(r.content for r in rendered_list)

        # Deduplicate instructions while preserving order
        seen_instructions = set()
        unique_instructions = []
        for r in rendered_list:
            if r.instruction and r.instruction not in seen_instructions:
                seen_instructions.add(r.instruction)
                unique_instructions.append(r.instruction)

        combined_instructions = "\n".join(unique_instructions)

        # Create a new RenderedContent with combined values
        # Note: Only instruction is preserved in frontmatter because:
        # - type: All workflow templates are "agent/instruction" (consistent)
        # - description: Combining descriptions doesn't make semantic sense
        # - instruction: This is the critical field that must be preserved and combined
        # frontmatter_length is 0 because this is a synthetic combined object with no source frontmatter
        first = rendered_list[0]
        return RenderedContent(
            content=combined_content,
            content_length=len(combined_content),
            frontmatter=Frontmatter(
                {"type": "agent/instruction", "instruction": combined_instructions} if combined_instructions else {}
            ),
            frontmatter_length=0,  # Synthetic combined object has no source frontmatter
            template_path=first.template_path,
            template_name=first.template_name,
        )
