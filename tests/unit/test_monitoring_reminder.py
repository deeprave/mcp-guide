"""Test for monitoring reminder functionality."""

import pytest

from mcp_guide.task_manager import EventType, TaskManager
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
        manager = TaskManager()
        task = WorkflowMonitorTask(".guide.yaml", manager)

        # Mock the workflow instruction system to avoid session dependency
        original_queue_workflow_instruction = None

        async def mock_queue_workflow_instruction(task_manager, template_pattern):
            # Simulate the instruction being queued
            await task_manager.queue_instruction(f"Mock reminder for {template_pattern}")

        # Patch the WorkflowTaskManager method
        from unittest.mock import patch

        with patch(
            "mcp_guide.workflow.task_manager.WorkflowTaskManager.queue_workflow_instruction",
            side_effect=mock_queue_workflow_instruction,
        ):
            # Simulate timer event
            result = await task.handle_event(EventType.TIMER, {"timer_interval": 300.0})

        assert result is True
        assert len(manager._pending_instructions) == 1
        assert "reminder" in manager._pending_instructions[0].lower()

    @pytest.mark.asyncio
    async def test_monitoring_reminder_no_duplicates(self) -> None:
        """Test that multiple timer events don't create duplicate reminders."""
        manager = TaskManager()
        task = WorkflowMonitorTask(".guide.yaml", manager)

        # Mock the workflow instruction system to avoid session dependency
        call_count = 0

        async def mock_queue_workflow_instruction(task_manager, template_pattern):
            nonlocal call_count
            call_count += 1
            # Simulate the instruction being queued
            await task_manager.queue_instruction(f"Mock reminder for {template_pattern}")

        # Patch the WorkflowTaskManager method
        from unittest.mock import patch

        with patch(
            "mcp_guide.workflow.task_manager.WorkflowTaskManager.queue_workflow_instruction",
            side_effect=mock_queue_workflow_instruction,
        ):
            # Simulate multiple timer events
            await task.handle_event(EventType.TIMER, {"timer_interval": 300.0})
            await task.handle_event(EventType.TIMER, {"timer_interval": 300.0})
            await task.handle_event(EventType.TIMER, {"timer_interval": 300.0})

        # Verify the workflow instruction was called multiple times
        assert call_count == 3
        # But TaskManager should have duplicate prevention, so only one instruction
        assert len(manager._pending_instructions) == 1
        assert "reminder" in manager._pending_instructions[0].lower()
