"""Tests for RetryTask."""

import time

import pytest

from mcp_guide.task_manager.interception import EventType
from mcp_guide.task_manager.manager import TaskManager


class TestRetryTask:
    """Test RetryTask functionality."""

    @pytest.mark.anyio
    async def test_retry_task_exists(self):
        """Test that RetryTask can be imported and instantiated."""
        from mcp_guide.tasks.retry_task import RetryTask

        task = RetryTask(TaskManager())
        assert task is not None

    @pytest.mark.anyio
    async def test_retry_task_has_protocol_methods(self):
        """Test that RetryTask implements TaskSubscriber protocol."""
        from mcp_guide.tasks.retry_task import RetryTask

        task = RetryTask(TaskManager())
        assert hasattr(task, "get_name")
        assert hasattr(task, "on_init")
        assert hasattr(task, "on_tool")
        assert hasattr(task, "handle_event")

    @pytest.mark.anyio
    async def test_retry_task_get_name(self):
        """Test that RetryTask returns correct name."""
        from mcp_guide.tasks.retry_task import RetryTask

        task = RetryTask(TaskManager())
        assert task.get_name() == "RetryTask"

    @pytest.mark.anyio
    async def test_retry_task_ignores_non_timer_events(self):
        """Test that RetryTask ignores non-timer events."""
        from mcp_guide.tasks.retry_task import RetryTask

        manager = TaskManager()
        task = RetryTask(manager)

        # Should not raise exception
        result = await task.handle_event(EventType.FS_COMMAND, {})
        assert result is None or result is False

    @pytest.mark.anyio
    async def test_retry_task_skips_retry_when_queue_not_empty(self):
        """Test that RetryTask skips retry when queue is not empty."""
        from mcp_guide.tasks.retry_task import RetryTask

        manager = TaskManager()
        task = RetryTask(manager)

        # Add instruction to queue
        await manager.queue_instruction("Test")

        # Handle timer event - should not retry
        await task.handle_event(EventType.TIMER, {"timer_interval": 60.0})

        # Queue should still have the original instruction only
        assert len(manager._pending_instructions) == 1

    @pytest.mark.anyio
    async def test_retry_task_calls_retry_when_queue_empty(self):
        """Test that RetryTask calls retry_unacknowledged when queue is empty."""
        from mcp_guide.tasks.retry_task import RetryTask

        manager = TaskManager()
        task = RetryTask(manager)

        # Queue tracked instruction
        instruction_id = await manager.queue_instruction_with_ack("Test instruction")
        # Clear queue to simulate dispatch
        manager._pending_instructions.clear()

        # Set last_sent_at to past to allow retry
        tracked = manager._tracked_instructions[instruction_id]
        tracked.last_sent_at = time.time() - 31.0

        # Handle timer event - should retry
        await task.handle_event(EventType.TIMER, {"timer_interval": 60.0})

        # Instruction should be requeued
        assert "Test instruction" in manager._pending_instructions
