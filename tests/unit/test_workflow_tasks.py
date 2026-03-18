"""Tests for workflow-specific task implementations."""

import pytest

from mcp_guide.task_manager import EventType
from mcp_guide.workflow.tasks import WorkflowMonitorTask


class TestWorkflowMonitorTask:
    """Test WorkflowMonitorTask functionality."""

    @pytest.fixture
    def monitor_task(self):
        return WorkflowMonitorTask(".guide.yaml")

    def test_workflow_monitor_task_creation(self, monitor_task) -> None:
        """Test WorkflowMonitorTask can be created."""
        assert monitor_task.get_name() == "WorkflowMonitorTask"

    @pytest.mark.anyio
    async def test_workflow_monitor_task_handles_events(self, monitor_task) -> None:
        """Test WorkflowMonitorTask handles events correctly."""
        # Test file content event handling
        result = await monitor_task.handle_event(
            EventType.FS_FILE_CONTENT, {"path": ".guide.yaml", "content": "phase: test\nissue: test-issue"}
        )
        assert result.result is True

    @pytest.mark.anyio
    async def test_workflow_monitor_task_ignores_unrelated_events(self, monitor_task) -> None:
        """Test WorkflowMonitorTask ignores unrelated events and leaves state unchanged."""
        import copy

        # Capture initial state before dispatching any events
        exclude = {"task_manager"}
        initial_filtered = {k: v for k, v in monitor_task.__dict__.items() if k not in exclude}

        # Non-matching file content event (different path)
        result_file_content = await monitor_task.handle_event(
            EventType.FS_FILE_CONTENT,
            {"path": "unrelated/config.yaml", "content": "phase: other\nissue: other-issue"},
        )
        assert result_file_content is None

        # Directory event should also be ignored
        result_directory = await monitor_task.handle_event(
            EventType.FS_DIRECTORY,
            {"path": ".guide", "action": "modified"},
        )
        assert result_directory is None

        # Ensure state has not changed after handling unrelated events
        # Exclude task_manager (contains asyncio.Task, not picklable and not relevant state)
        final_filtered = {k: v for k, v in monitor_task.__dict__.items() if k not in exclude}
        assert copy.deepcopy(final_filtered) == copy.deepcopy(initial_filtered)
