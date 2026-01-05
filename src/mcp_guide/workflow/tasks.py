"""Workflow-specific task implementations."""

from typing import TYPE_CHECKING, Any, Optional

from pydantic import ValidationError

from mcp_core.mcp_log import get_logger
from mcp_guide.task_manager import DataType, TaskState, TaskType

if TYPE_CHECKING:
    from mcp_guide.task_manager import TaskManager

logger = get_logger(__name__)


class WorkflowMonitorTask:
    """Scheduled background monitoring task for workflow state changes."""

    def __init__(self, workflow_file_path: str, task_manager: Optional["TaskManager"] = None):
        self.workflow_file_path = workflow_file_path
        self.timeout: Optional[float] = None
        self.task_type = TaskType.SCHEDULED
        self.state = TaskState.IDLE
        self.task_manager = task_manager
        self._cached_content: Optional[str] = None
        self._cached_mtime: Optional[float] = None
        self._paused = False

    async def task_start(self) -> tuple[TaskState, Optional[str]]:
        """Start monitoring workflow file."""
        self.state = TaskState.ACTIVE
        return (TaskState.ACTIVE, None)

    async def response(self, data: Any) -> tuple[TaskState, Optional[str]]:
        """Handle response data."""
        return (TaskState.COMPLETED, None)

    async def timeout_expired(self) -> tuple[TaskState, Optional[str]]:
        """Handle timeout expiry."""
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

    async def process_data(self, data_type: DataType, data: dict[str, Any]) -> None:
        """Process workflow file data and update cached state."""
        if self._paused:
            return  # Skip processing when paused

        if data_type == DataType.FILE_CONTENT:
            current_mtime = data.get("mtime")
            content = data.get("content", "")

            # Cache content and mtime on the task instance
            self._cached_content = content
            self._cached_mtime = current_mtime

            # Only process if file has changed
            cached_mtime = self.task_manager.get_cached_data("workflow_state_mtime") if self.task_manager else None
            if current_mtime != cached_mtime:
                if content.strip():
                    try:
                        import yaml

                        from mcp_guide.workflow.schema import WorkflowState

                        # Parse YAML content into WorkflowState model
                        yaml_data = yaml.safe_load(content)
                        workflow_state = WorkflowState.model_validate(yaml_data)

                        # Cache the parsed state and mtime
                        if self.task_manager:
                            self.task_manager.set_cached_data("workflow_state", workflow_state)
                            self.task_manager.set_cached_data("workflow_state_mtime", current_mtime)

                            # Queue instruction for state change
                            self.task_manager.queue_instruction(
                                f"Workflow phase changed to {workflow_state.phase}. "
                                f"Use get_content tool to review current phase rules."
                            )

                        self.state = TaskState.ACTIVE
                    except yaml.YAMLError as e:
                        logger.warning(f"Invalid YAML in workflow state file: {e}")
                        # Keep existing state, don't update cache
                        return
                    except ValidationError as e:
                        logger.warning(f"Invalid workflow state format: {e}")
                        # Keep existing state, don't update cache
                        return
                    except Exception as e:
                        logger.error(f"Unexpected error parsing workflow state: {e}")
                        # Keep existing state, don't update cache
                        return
                else:
                    # Empty content - clear cache
                    if self.task_manager:
                        self.task_manager.clear_cached_data("workflow_state")
                        self.task_manager.clear_cached_data("workflow_state_mtime")

    def check_workflow_file_interest(self, data_type: DataType, data: dict[str, Any]) -> bool:
        """Check if data is for our workflow file."""
        if data_type != DataType.FILE_CONTENT:
            return False
        path = data.get("path", "")
        return isinstance(path, str) and path.endswith(self.workflow_file_path)


class WorkflowUpdateTask:
    """Active task for handling workflow state changes."""

    def __init__(self, component_path: str, task_manager: Optional["TaskManager"] = None):
        self.component_path = component_path
        self.task_type = TaskType.ACTIVE
        self.timeout: Optional[float] = 30.0
        self.state = TaskState.IDLE
        self.task_manager = task_manager
        self._task_completion_data: Optional[dict[str, Any]] = None

    async def task_start(self) -> tuple[TaskState, Optional[str]]:
        """Start workflow update task."""
        self.state = TaskState.ACTIVE
        instruction = "Please provide task completion data"
        if self.task_manager:
            self.task_manager.queue_instruction(instruction)
        return (TaskState.ACTIVE, instruction)

    async def response(self, data: Any) -> tuple[TaskState, Optional[str]]:
        """Handle response data."""
        return (TaskState.COMPLETED, None)

    async def timeout_expired(self) -> tuple[TaskState, Optional[str]]:
        """Handle timeout expiry."""
        self.state = TaskState.IDLE
        return (TaskState.IDLE, "Workflow update timed out")

    async def completed(self) -> tuple[TaskState, Optional[str]]:
        """Handle task completion."""
        self.state = TaskState.COMPLETED
        return (TaskState.COMPLETED, None)

    async def pause(self) -> None:
        """Pause the task (no-op for active tasks)."""
        pass

    async def resume(self) -> None:
        """Resume the task (no-op for active tasks)."""
        pass

    async def process_data(self, data_type: DataType, data: dict[str, Any]) -> None:
        """Process task completion data and validate."""
        if data_type == DataType.FILE_CONTENT:
            # Validate task completion data
            content = data.get("content", "")
            if self._validate_task_completion(content):
                self._task_completion_data = data
                self.state = TaskState.COMPLETED

    def check_task_file_interest(self, data_type: DataType, data: dict[str, Any]) -> bool:
        """Check if data is for component task files."""
        if data_type != DataType.FILE_CONTENT:
            return False
        path = data.get("path", "")
        return isinstance(path, str) and self.component_path in path and path.endswith("tasks.md")

    def _validate_task_completion(self, content: str) -> bool:
        """Validate task completion format."""
        if not isinstance(content, str) or not content.strip():
            return False
        return "- [x]" in content
