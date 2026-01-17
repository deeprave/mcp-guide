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

    @pytest.mark.asyncio
    async def test_workflow_monitor_task_handles_events(self, monitor_task) -> None:
        """Test WorkflowMonitorTask handles events correctly."""
        # Test file content event handling
        result = await monitor_task.handle_event(
            EventType.FS_FILE_CONTENT, {"path": ".guide.yaml", "content": "phase: test\nissue: test-issue"}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_workflow_monitor_task_ignores_unrelated_events(self, monitor_task) -> None:
        """Test WorkflowMonitorTask ignores unrelated events and leaves state unchanged."""
        import copy

        # Capture initial state snapshot
        initial_state = copy.deepcopy(monitor_task.__dict__)

        # Non-matching file content event (different path)
        result_file_content = await monitor_task.handle_event(
            EventType.FS_FILE_CONTENT,
            {"path": "unrelated/config.yaml", "content": "phase: other\nissue: other-issue"},
        )
        assert result_file_content is False

        # Directory event should also be ignored
        result_directory = await monitor_task.handle_event(
            EventType.FS_DIRECTORY,
            {"path": ".guide", "action": "modified"},
        )
        assert result_directory is False

        # Ensure state has not changed after handling unrelated events
        final_state = copy.deepcopy(monitor_task.__dict__)
        assert final_state == initial_state

    def test_detect_openspec_change_with_matching_directory(self, monitor_task, tmp_path) -> None:
        """Test OpenSpec change detection with matching directory."""
        import os

        # Create openspec/changes/test-issue directory
        (tmp_path / "openspec" / "changes" / "test-issue").mkdir(parents=True)

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            assert monitor_task._detect_openspec_change("test-issue") is True
        finally:
            os.chdir(old_cwd)

    def test_detect_openspec_change_with_no_directory(self, monitor_task) -> None:
        """Test OpenSpec change detection with no matching directory."""
        assert monitor_task._detect_openspec_change("nonexistent-issue") is False

    def test_detect_openspec_change_with_none_issue(self, monitor_task) -> None:
        """Test OpenSpec change detection with None issue name."""
        assert monitor_task._detect_openspec_change(None) is False
