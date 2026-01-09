"""Workflow-specific task implementations."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from mcp_core.mcp_log import get_logger
from mcp_guide.workflow.parser import parse_workflow_state

if TYPE_CHECKING:
    from mcp_guide.task_manager import EventType, TaskManager

    # Import WorkflowTaskManager only for type checking to avoid circular import:
    # WorkflowTaskManager -> WorkflowMonitorTask -> WorkflowTaskManager

logger = get_logger(__name__)

# Workflow monitoring interval in seconds
WORKFLOW_INTERVAL = 120.0


class WorkflowMonitorTask:
    """Scheduled background monitoring task for workflow state changes."""

    def get_name(self) -> str:
        """Get a readable name for the task."""
        return "WorkflowMonitorTask"

    def __init__(
        self,
        workflow_file_path: str,
        task_manager: Optional["TaskManager"] = None,
    ):
        self.workflow_file_path = workflow_file_path

        # TaskManager is a singleton, so get it if not provided
        if task_manager is None:
            from mcp_guide.task_manager import get_task_manager

            task_manager = get_task_manager()
        self.task_manager: "TaskManager" = task_manager

        self._cached_content: Optional[str] = None
        self._cached_mtime: Optional[float] = None

    async def handle_event(self, event_type: "EventType", data: dict[str, Any]) -> bool:
        """Handle task manager events."""
        from mcp_guide.task_manager.interception import EventType

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
        # Import at runtime to avoid circular import: WorkflowTaskManager -> WorkflowMonitorTask -> WorkflowTaskManager
        from mcp_guide.workflow.task_manager import WorkflowTaskManager

        # Use the existing workflow instruction system
        await WorkflowTaskManager.queue_workflow_instruction(self.task_manager, "monitoring-reminder")

    async def _process_workflow_content(self, content: str) -> None:
        """Process workflow file content and update cached state."""
        logger.trace("_process_workflow_content ASYNC method called")
        try:
            # Parse the workflow state
            logger.trace("About to parse workflow state")
            if workflow_state := parse_workflow_state(content):
                logger.trace(f"Parsed workflow state: phase={workflow_state.phase}, issue={workflow_state.issue}")

                # Cache the workflow state in TaskManager
                logger.trace("About to cache workflow state")
                self.task_manager.set_cached_data("workflow_state", workflow_state)
                logger.trace("Workflow state cached in TaskManager")

                # Always queue monitoring reminder instruction when workflow content is processed
                # Import at runtime to avoid circular import: WorkflowTaskManager -> WorkflowMonitorTask -> WorkflowTaskManager
                from mcp_guide.workflow.task_manager import WorkflowTaskManager

                logger.trace("About to queue monitoring-result instruction")
                await WorkflowTaskManager.queue_workflow_instruction(self.task_manager, "monitoring-result")
                logger.trace("Workflow monitoring reminder instruction queued")
            else:
                logger.warning("Failed to parse workflow state - not caching or queuing instructions")

        except Exception as e:
            logger.warning(f"Failed to process workflow content: {e}")
            import traceback

            logger.warning(f"Workflow content processing traceback: {traceback.format_exc()}")
