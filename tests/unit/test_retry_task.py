"""Tests for RetryTask."""

import time

import pytest

from mcp_guide.task_manager.interception import EventType
from mcp_guide.task_manager.manager import TaskManager


class TestRetryTask:
    """Test RetryTask functionality."""

    @pytest.mark.anyio
    async def test_retry_task_exists(self, task_manager: TaskManager):
        """Test that RetryTask can be imported and instantiated."""
        from mcp_guide.tasks.retry_task import RetryTask

        task = RetryTask(task_manager)
        assert task is not None

    @pytest.mark.anyio
    async def test_retry_task_has_protocol_methods(self, task_manager: TaskManager):
        """Test that RetryTask implements TaskSubscriber protocol."""
        from mcp_guide.tasks.retry_task import RetryTask

        task = RetryTask(task_manager)
        assert hasattr(task, "get_name")
        assert hasattr(task, "on_init")
        assert hasattr(task, "on_tool")
        assert hasattr(task, "handle_event")

    @pytest.mark.anyio
    async def test_retry_task_get_name(self, task_manager: TaskManager):
        """Test that RetryTask returns correct name."""
        from mcp_guide.tasks.retry_task import RetryTask

        task = RetryTask(task_manager)
        assert task.get_name() == "RetryTask"

    @pytest.mark.anyio
    async def test_retry_task_ignores_non_timer_events(self, task_manager: TaskManager):
        """Test that RetryTask ignores non-timer events."""
        from mcp_guide.tasks.retry_task import RetryTask

        task = RetryTask(task_manager)

        # Should not raise exception
        result = await task.handle_event(EventType.FS_COMMAND, {})
        assert result is None

    @pytest.mark.anyio
    async def test_retry_task_skips_retry_when_queue_not_empty(self, task_manager: TaskManager):
        """Test that RetryTask skips retry when queue is not empty."""
        from mcp_guide.tasks.retry_task import RetryTask

        task = RetryTask(task_manager)

        # Add instruction to queue
        await task_manager.queue_instruction("Test")

        # Handle timer event - should not retry
        await task.handle_event(EventType.TIMER, {"timer_interval": 60.0})

        # Queue should still have the original instruction only
        assert len(task_manager._pending_instructions) == 1

    @pytest.mark.anyio
    async def test_retry_task_calls_retry_when_queue_empty(self, task_manager: TaskManager):
        """Test that RetryTask calls retry_unacknowledged when queue is empty."""
        from mcp_guide.tasks.retry_task import RetryTask

        task = RetryTask(task_manager)

        # Queue tracked instruction
        instruction_id = await task_manager.queue_instruction_with_ack("Test instruction")
        # Clear queue to simulate dispatch
        task_manager._pending_instructions.clear()

        # Set last_sent_at to past to allow retry
        tracked = task_manager._tracked_instructions[instruction_id]
        tracked.last_sent_at = time.time() - 31.0

        # Handle timer event - should retry
        await task.handle_event(EventType.TIMER, {"timer_interval": 60.0})

        # Instruction should be requeued
        assert "Test instruction" in task_manager._pending_instructions

    @pytest.mark.anyio
    async def test_retry_task_respects_grace_period(self, task_manager: TaskManager):
        """Test that RetryTask respects grace period before unsubscribing."""
        from mcp_guide.tasks.retry_task import RetryTask

        task = RetryTask(task_manager)

        # Verify task is subscribed
        assert task_manager.get_subscription_count() == 1

        # First tick - should not unsubscribe (within grace period)
        await task.handle_event(EventType.TIMER, {"timer_interval": 60.0})
        assert task_manager.get_subscription_count() == 1

        # Second tick - should not unsubscribe (within grace period)
        await task.handle_event(EventType.TIMER, {"timer_interval": 60.0})
        assert task_manager.get_subscription_count() == 1

        # Third tick - should unsubscribe (after grace period)
        await task.handle_event(EventType.TIMER, {"timer_interval": 60.0})
        assert task_manager.get_subscription_count() == 0

    @pytest.mark.anyio
    async def test_retry_task_does_not_unsubscribe_with_other_subscribers(self, task_manager: TaskManager):
        """Test that RetryTask does not unsubscribe when other subscribers exist."""
        from mcp_guide.tasks.retry_task import RetryTask

        task = RetryTask(task_manager)

        # Add another subscriber
        class DummySubscriber:
            def get_name(self):
                return "DummySubscriber"

            async def on_init(self):
                pass

            async def on_tool(self):
                pass

            async def handle_event(self, event_type, data):
                return None

        dummy = DummySubscriber()
        task_manager.subscribe(dummy, EventType.TIMER, timer_interval=120.0)

        # Verify both tasks are subscribed
        assert task_manager.get_subscription_count() == 2

        # Tick past grace period
        for _ in range(3):
            await task.handle_event(EventType.TIMER, {"timer_interval": 60.0})

        # RetryTask should still be subscribed
        assert task_manager.get_subscription_count() == 2
