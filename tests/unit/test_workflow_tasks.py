"""Tests for workflow-specific task implementations."""

import pytest

from mcp_guide.task_manager import TaskState
from mcp_guide.workflow.tasks import WorkflowMonitorTask


class TestWorkflowMonitorTask:
    """Test WorkflowMonitorTask functionality."""

    @pytest.fixture
    def monitor_task(self):
        return WorkflowMonitorTask(".guide.yaml")

    async def test_task_start(self, monitor_task):
        """Test task start returns active state."""
        state, instruction = await monitor_task.task_start()
        assert state == TaskState.ACTIVE
        assert instruction is None
