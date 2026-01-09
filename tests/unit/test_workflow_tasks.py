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
