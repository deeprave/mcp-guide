"""Workflow manager for coordinating workflow tasks with TaskManager."""

from typing import Optional

from mcp_guide.feature_flags.project_flags import ProjectFlags
from mcp_guide.task_manager import DataType, TaskManager
from mcp_guide.workflow.tasks import WorkflowMonitorTask, WorkflowUpdateTask


class WorkflowManager:
    """Manages workflow coordination using TaskManager."""

    def __init__(self, task_manager: TaskManager, project_flags: ProjectFlags):
        self.task_manager = task_manager
        self.project_flags = project_flags
        self._monitor_task: Optional[WorkflowMonitorTask] = None
        self._update_task: Optional[WorkflowUpdateTask] = None

    async def is_workflow_enabled(self) -> bool:
        """Check if workflow tracking is enabled."""
        workflow_file = await self.project_flags.get("workflow-file")
        return workflow_file is not None

    async def start_monitoring(self) -> None:
        """Start workflow monitoring if enabled."""
        if not await self.is_workflow_enabled():
            return

        workflow_file = await self.project_flags.get("workflow-file")
        if workflow_file and not self._monitor_task:
            self._monitor_task = WorkflowMonitorTask(str(workflow_file))

            # Register interest in workflow file changes
            self.task_manager.register_interest(
                self._monitor_task, DataType.FILE_CONTENT, self._monitor_task.check_workflow_file_interest
            )

            await self.task_manager.register_task(self._monitor_task)

    async def start_update_task(self, component_path: str) -> None:
        """Start workflow update task for component."""
        if not await self.is_workflow_enabled():
            return

        if self._update_task:
            # Complete existing update task
            self.task_manager.complete_task(self._update_task)

        self._update_task = WorkflowUpdateTask(component_path)

        # Register interest in component task files
        self.task_manager.register_interest(
            self._update_task, DataType.FILE_CONTENT, self._update_task.check_task_file_interest
        )

        await self.task_manager.register_task(self._update_task)

    def stop_monitoring(self) -> None:
        """Stop workflow monitoring."""
        if self._monitor_task:
            self.task_manager.complete_task(self._monitor_task)
            self._monitor_task = None

    def stop_update_task(self) -> None:
        """Stop current update task."""
        if self._update_task:
            self.task_manager.complete_task(self._update_task)
            self._update_task = None
