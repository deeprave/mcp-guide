"""Tests for RetryTask."""

import pytest

from mcp_guide.result import Result
from mcp_guide.task_manager.interception import EventType
from mcp_guide.task_manager.manager import TaskManager


class TestRetryTask:
    """Test RetryTask functionality."""

    @pytest.mark.anyio
    async def test_retry_is_delivered_only_on_an_idle_timer_tick(self, task_manager, monkeypatch):
        from mcp_guide.tasks.retry_task import RetryTask

        now = 100.0
        monkeypatch.setattr("mcp_guide.task_manager.manager.time.time", lambda: now)
        task = RetryTask(task_manager)
        await task_manager.queue_instruction_with_ack("Retry me")
        assert (await task_manager.process_result(Result.ok())).additional_agent_instructions == "Retry me"
        now += 31

        assert await task.handle_event(EventType.FS_COMMAND, {}) is None
        assert task_manager.is_queue_empty()
        await task_manager.queue_instruction("Busy")
        await task.handle_event(EventType.TIMER, {})
        assert (await task_manager.process_result(Result.ok())).additional_agent_instructions == "Busy"
        assert task_manager.is_queue_empty()

        await task.handle_event(EventType.TIMER, {})
        assert (await task_manager.process_result(Result.ok())).additional_agent_instructions == "Retry me"
        assert task_manager.is_queue_empty()

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
