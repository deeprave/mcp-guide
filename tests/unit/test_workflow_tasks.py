"""Tests for workflow-specific task implementations."""

import pytest

from mcp_guide.task_manager import DataType, TaskState
from mcp_guide.workflow.tasks import WorkflowMonitorTask, WorkflowUpdateTask


class TestWorkflowMonitorTask:
    """Test WorkflowMonitorTask functionality."""

    @pytest.fixture
    def monitor_task(self):
        """Create WorkflowMonitorTask instance."""
        return WorkflowMonitorTask("workflow-state.json")

    async def test_task_start(self, monitor_task):
        """Test task start sets active state."""
        state, instruction = await monitor_task.task_start()
        assert state == TaskState.ACTIVE
        assert monitor_task.state == TaskState.ACTIVE

    def test_check_workflow_file_interest_match(self, monitor_task):
        """Test interest check matches workflow file."""
        data = {"path": "/project/workflow-state.json", "content": "{}"}
        result = monitor_task.check_workflow_file_interest(DataType.FILE_CONTENT, data)
        assert result is True

    def test_check_workflow_file_interest_no_match(self, monitor_task):
        """Test interest check rejects other files."""
        data = {"path": "/project/other-file.txt", "content": "data"}
        result = monitor_task.check_workflow_file_interest(DataType.FILE_CONTENT, data)
        assert result is False

    def test_check_workflow_file_interest_wrong_type(self, monitor_task):
        """Test interest check rejects wrong data type."""
        data = {"entries": []}
        result = monitor_task.check_workflow_file_interest(DataType.DIRECTORY_LISTING, data)
        assert result is False

    async def test_process_data_caches_content(self, monitor_task):
        """Test process_data caches workflow file content."""
        data = {"path": "/project/workflow-state.json", "content": "{}", "mtime": 1234567890}
        await monitor_task.process_data(DataType.FILE_CONTENT, data)

        assert monitor_task._cached_content == "{}"
        assert monitor_task._cached_mtime == 1234567890
        assert monitor_task.state == TaskState.ACTIVE


class TestWorkflowUpdateTask:
    """Test WorkflowUpdateTask functionality."""

    @pytest.fixture
    def update_task(self):
        """Create WorkflowUpdateTask instance."""
        return WorkflowUpdateTask("openspec/changes/test-component")

    async def test_task_start_with_instruction(self, update_task):
        """Test task start returns instruction."""
        state, instruction = await update_task.task_start()
        assert state == TaskState.ACTIVE
        assert instruction == "Please provide task completion data"
        assert update_task.state == TaskState.ACTIVE

    def test_check_task_file_interest_match(self, update_task):
        """Test interest check matches component task file."""
        data = {"path": "openspec/changes/test-component/tasks.md", "content": "- [x] Task 1"}
        result = update_task.check_task_file_interest(DataType.FILE_CONTENT, data)
        assert result is True

    def test_check_task_file_interest_no_match(self, update_task):
        """Test interest check rejects other files."""
        data = {"path": "openspec/changes/other-component/tasks.md", "content": "data"}
        result = update_task.check_task_file_interest(DataType.FILE_CONTENT, data)
        assert result is False

    async def test_process_data_validates_completion(self, update_task):
        """Test process_data validates task completion."""
        data = {"path": "openspec/changes/test-component/tasks.md", "content": "- [x] Completed task"}
        await update_task.process_data(DataType.FILE_CONTENT, data)

        assert update_task._task_completion_data == data
        assert update_task.state == TaskState.COMPLETED

    async def test_process_data_rejects_incomplete(self, update_task):
        """Test process_data rejects incomplete tasks."""
        data = {"path": "openspec/changes/test-component/tasks.md", "content": "- [ ] Incomplete task"}
        await update_task.process_data(DataType.FILE_CONTENT, data)

        assert update_task._task_completion_data is None
        assert update_task.state == TaskState.IDLE

    async def test_timeout_expired_returns_message(self, update_task):
        """Test timeout returns appropriate message."""
        state, instruction = await update_task.timeout_expired()
        assert state == TaskState.IDLE
        assert instruction == "Workflow update timed out"
        assert update_task.state == TaskState.IDLE
