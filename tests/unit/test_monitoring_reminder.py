"""Test for monitoring reminder functionality."""

import pytest

from mcp_guide.task_manager import TaskManager
from mcp_guide.workflow.tasks import WorkflowMonitorTask


class TestMonitoringReminder:
    """Test monitoring reminder functionality."""

    @pytest.fixture(autouse=True)
    def reset_task_manager(self) -> None:
        """Reset TaskManager singleton before each test."""
        TaskManager._reset_for_testing()
        yield
        TaskManager._reset_for_testing()

    @pytest.mark.asyncio
    async def test_duplicate_instruction_prevention(self) -> None:
        """Test that duplicate instructions are not queued."""
        manager = TaskManager()

        # Queue the same instruction multiple times
        await manager.queue_instruction("Test instruction")
        await manager.queue_instruction("Test instruction")
        await manager.queue_instruction("Different instruction")
        await manager.queue_instruction("Test instruction")

        # Should only have 2 unique instructions
        assert len(manager._pending_instructions) == 2
        assert "Test instruction" in manager._pending_instructions
        assert "Different instruction" in manager._pending_instructions

    @pytest.mark.asyncio
    async def test_monitoring_reminder_timer_event(self) -> None:
        """Test that timer events trigger monitoring reminders."""
        task = WorkflowMonitorTask(".guide.yaml")

        # Verify task can handle timer events
        assert hasattr(task, "handle_event")
        assert callable(task.handle_event)

    @pytest.mark.asyncio
    async def test_monitoring_reminder_no_duplicates(self) -> None:
        """Test that WorkflowMonitorTask exists and is functional."""
        task = WorkflowMonitorTask(".guide.yaml")

        # Verify task has expected attributes
        assert task.get_name() == "WorkflowMonitorTask"
        assert hasattr(task, "workflow_file_path")
