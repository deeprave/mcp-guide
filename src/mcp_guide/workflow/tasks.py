"""Workflow-specific task implementations."""

from typing import TYPE_CHECKING, Any, Optional

from mcp_core.mcp_log import get_logger
from mcp_guide.task_manager import TaskState, TaskType

if TYPE_CHECKING:
    from mcp_core.result import Result
    from mcp_guide.task_manager import EventType, TaskManager

logger = get_logger(__name__)


class WorkflowMonitorTask:
    """Scheduled background monitoring task for workflow state changes."""

    def __init__(
        self,
        workflow_file_path: str,
        task_manager: Optional["TaskManager"] = None,
        allowed_write_paths: Optional[list[str]] = None,
    ):
        # Validate path before storing if security context is available
        if allowed_write_paths:
            from mcp_guide.workflow.flags import validate_workflow_file_path

            self.workflow_file_path = validate_workflow_file_path(workflow_file_path, allowed_write_paths)
        else:
            self.workflow_file_path = workflow_file_path
        self.timeout: Optional[float] = None
        self.task_type = TaskType.SCHEDULED
        self.state = TaskState.IDLE

        # TaskManager is a singleton, so get it if not provided
        if task_manager is None:
            from mcp_guide.task_manager import get_task_manager

            task_manager = get_task_manager()
        self.task_manager: "TaskManager" = task_manager

        self._cached_content: Optional[str] = None
        self._cached_mtime: Optional[float] = None
        self._paused = False

    async def _normalize_path(self, path: str) -> str:
        """Normalize path to absolute for comparison."""
        from pathlib import Path

        path_obj = Path(path)
        if path_obj.is_absolute():
            return str(path_obj.resolve())

        # Relative path - resolve against project root
        from mcp_guide.mcp_context import resolve_project_path

        project_root = await resolve_project_path()
        return str((project_root / path).resolve())

    async def task_start(self) -> tuple[TaskState, Optional[str]]:
        """Start monitoring workflow file."""
        self.state = TaskState.ACTIVE

        # Register interest in file content events for our workflow file
        from mcp_guide.task_manager.interception import EventType

        await self.task_manager.subscribe(self, EventType.FS_FILE_CONTENT, timer_interval=None)

        # Subscribe to timer events for monitoring reminders (300 second interval)
        await self.task_manager.subscribe(self, EventType.TIMER, timer_interval=300.0)

        logger.trace(
            f"WorkflowMonitorTask registered interest in file content and timer events for: {self.workflow_file_path}"
        )

        return (TaskState.ACTIVE, None)

    async def handle_event(self, event_type: "EventType", data: dict[str, Any]) -> bool:
        """Handle task manager events."""
        from mcp_guide.task_manager.interception import EventType

        # Handle timer events for monitoring reminders
        if event_type & EventType.TIMER:
            await self._handle_monitoring_reminder()
            return True

        # Check if the file content is for our workflow file
        path = data.get("path")
        if isinstance(path, str) and await self._normalize_path(path) == await self._normalize_path(
            self.workflow_file_path
        ):
            # Process the data directly - no need for async task
            self._process_workflow_content_sync(data.get("content", ""))
            return True
        return False

    def _process_workflow_content_sync(self, content: str) -> None:
        """Process workflow file content synchronously."""
        if self._paused:
            return

        logger.trace(f"Processing workflow file content: {len(content)} chars")

        try:
            from mcp_guide.workflow.parser import parse_workflow_state

            # Parse the workflow state
            workflow_state = parse_workflow_state(content)
            if workflow_state:
                logger.trace(f"Parsed workflow state: phase={workflow_state.phase}, issue={workflow_state.issue}")

                # Cache the workflow state in TaskManager
                self.task_manager.set_cached_data("workflow_state", workflow_state)
            logger.trace("Workflow state cached in TaskManager")

        except Exception as e:
            logger.warning(f"Failed to process workflow content: {e}")
            import traceback

            logger.warning(f"Workflow content processing traceback: {traceback.format_exc()}")

    async def _handle_monitoring_reminder(self) -> None:
        """Handle timer event for monitoring reminders."""
        if self._paused:
            return

        logger.trace("Timer event triggered - queuing monitoring reminder")

        # Queue a simple monitoring reminder message
        reminder_message = "This is a reminder that you must send the content of .guide.yaml using the send_file_content tool whenever it is updated."
        await self.task_manager.queue_instruction(reminder_message)

    async def response(self, data: Any) -> tuple[TaskState, Optional[str]]:
        """Handle response data."""
        return (TaskState.COMPLETED, None)

    async def timeout_expired(self) -> tuple[TaskState, Optional[str]]:
        """Handle timeout expiry (not used since timeout is None)."""
        return (TaskState.IDLE, None)

    async def completed(self) -> tuple[TaskState, Optional[str]]:
        """Handle task completion."""
        return (TaskState.IDLE, None)

    async def pause(self) -> None:
        """Pause the scheduled task."""
        self._paused = True

    async def resume(self) -> None:
        """Resume the scheduled task."""
        self._paused = False

    async def process_data(self, data_type: "EventType", data: dict[str, Any]) -> None:
        """Process agent data and update task state."""
        if self._paused:
            return

        logger.trace(f"WorkflowMonitorTask processing data: {data_type}, path={data.get('path')}")

        # Process workflow file content
        from mcp_guide.task_manager.interception import EventType

        if data_type == EventType.FS_FILE_CONTENT and await self._normalize_path(
            data.get("path", "")
        ) == await self._normalize_path(self.workflow_file_path):
            content = data.get("content", "")
            logger.trace(f"Processing workflow file content: {len(content)} chars")
            await self._process_workflow_content(content)

    async def _process_workflow_content(self, content: str) -> None:
        """Process workflow file content and update cached state."""
        try:
            from mcp_guide.workflow.parser import parse_workflow_state

            # Parse the workflow state
            workflow_state = parse_workflow_state(content)
            if workflow_state:
                logger.trace(f"Parsed workflow state: phase={workflow_state.phase}, issue={workflow_state.issue}")

                # Cache the workflow state in TaskManager
                self.task_manager.set_cached_data("workflow_state", workflow_state)
            logger.trace("Workflow state cached in TaskManager")

            # Always queue monitoring reminder instruction when workflow content is processed
            from mcp_guide.workflow.task_manager import WorkflowTaskManager

            await WorkflowTaskManager.queue_workflow_instruction(self.task_manager, "monitoring-result")
            logger.trace("Workflow monitoring reminder instruction queued")

        except Exception as e:
            logger.warning(f"Failed to process workflow content: {e}")
            import traceback

            logger.warning(f"Workflow content processing traceback: {traceback.format_exc()}")

    async def process_result(self, result: "Result[Any]") -> "Result[Any]":
        """Process workflow file result and update cached state."""
        if self._paused or not result.success:
            return result

        if not await self._is_workflow_file_result(result):
            return result

        await self._update_workflow_state(result)
        return result

    async def _is_workflow_file_result(self, result: "Result[Any]") -> bool:
        """Check if result is for our workflow file."""
        if not result.value or not isinstance(result.value, dict):
            return False
        path = result.value.get("path", "")
        return isinstance(path, str) and await self._normalize_path(path) == await self._normalize_path(
            self.workflow_file_path
        )

    async def _update_workflow_state(self, result: "Result[Any]") -> None:
        """Update workflow state from file content."""
        if not result.value or not isinstance(result.value, dict):
            return

        data = result.value
        current_mtime = data.get("mtime")
        content = data.get("content", "")

        # Cache content and mtime on the task instance
        self._cached_content = content
        self._cached_mtime = current_mtime

        # Only process if file has changed
        cached_mtime = self.task_manager.get_cached_data("workflow_state_mtime")
        if current_mtime != cached_mtime:
            if content.strip():
                from mcp_guide.workflow.parser import parse_workflow_state

                workflow_state = parse_workflow_state(content)
                if workflow_state:
                    # Cache the parsed state and mtime
                    self.task_manager.set_cached_data("workflow_state", workflow_state)
                    self.task_manager.set_cached_data("workflow_state_mtime", current_mtime)

                    # Render monitoring-result template
                    await self._queue_monitoring_result_instruction()

                self.state = TaskState.ACTIVE
            else:
                # Empty content - clear cache
                self.task_manager.clear_cached_data("workflow_state")
                self.task_manager.clear_cached_data("workflow_state_mtime")

    async def _queue_monitoring_result_instruction(self) -> None:
        """Queue monitoring result instruction using template rendering."""
        from mcp_guide.workflow.task_manager import WorkflowTaskManager

        await WorkflowTaskManager.queue_workflow_instruction(self.task_manager, "monitoring-result")
