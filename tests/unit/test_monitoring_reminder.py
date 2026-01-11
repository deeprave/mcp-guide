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

        async def mock_render_workflow_template(template_pattern):
            # Simulate the template being rendered
            return f"Mock reminder for {template_pattern}"

        # Patch the WorkflowTaskManager method
        from unittest.mock import patch

        with patch(
            "mcp_guide.workflow.task_manager.WorkflowTaskManager.render_workflow_template",
            side_effect=mock_render_workflow_template,
        ) as mock_render:
            # Simulate timer event
            result = await task.handle_event(EventType.TIMER, {"timer_interval": 300.0})

        assert result is True
        assert len(manager._pending_instructions) == 1
        assert "reminder" in manager._pending_instructions[0].lower()

        # Verify template rendering was called with correct pattern
        mock_render.assert_called_once_with("monitoring-reminder")

    @pytest.mark.asyncio
    async def test_monitoring_reminder_no_duplicates(self) -> None:
        """Test that multiple timer events don't create duplicate reminders."""
        manager = TaskManager()
        task = WorkflowMonitorTask(".guide.yaml", manager)

        # Mock the workflow template rendering system to avoid session dependency
        async def mock_render_workflow_template(template_pattern):
            # Simulate the template being rendered
            return f"Mock reminder for {template_pattern}"

        # Patch the WorkflowTaskManager method
        from unittest.mock import patch

        with patch(
            "mcp_guide.workflow.task_manager.WorkflowTaskManager.render_workflow_template",
            side_effect=mock_render_workflow_template,
        ) as mock_render:
            # Simulate multiple timer events
            await task.handle_event(EventType.TIMER, {"timer_interval": 300.0})
            await task.handle_event(EventType.TIMER, {"timer_interval": 300.0})
            await task.handle_event(EventType.TIMER, {"timer_interval": 300.0})

        # Verify the workflow instruction was called multiple times
        assert mock_render.call_count == 3
        # Verify all calls were with the correct template pattern
        for call in mock_render.call_args_list:
            assert call[0][0] == "monitoring-reminder"
        # But TaskManager should have duplicate prevention, so only one instruction
        assert len(manager._pending_instructions) == 1
        assert "reminder" in manager._pending_instructions[0].lower()
