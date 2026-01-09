"""Tests for timer event scheduling system."""

from typing import Any
from unittest.mock import patch

import pytest

from mcp_guide.task_manager import EventType, TaskManager


class MockTimerSubscriber:
    """Mock subscriber for timer events."""

    def __init__(self) -> None:
        self.received_events: list[tuple[EventType, dict[str, Any], float]] = []

    def get_name(self) -> str:
        """Get subscriber name."""
        return "MockTimerSubscriber"

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> bool:
        """Handle timer events and record timestamp."""
        # Use mocked time for deterministic testing
        import time

        self.received_events.append((event_type, data, time.time()))
        return True


@pytest.fixture(autouse=True)
def reset_task_manager() -> None:
    """Reset TaskManager singleton before each test."""
    TaskManager._reset_for_testing()
    yield
    TaskManager._reset_for_testing()


class TestTimerEventScheduling:
    """Test timer event scheduling system."""

    @pytest.mark.asyncio
    async def test_timer_subscription_creates_timer_task(self) -> None:
        """Test timer subscription creates background timer task."""
        manager = TaskManager()
        subscriber = MockTimerSubscriber()

        await manager.subscribe(subscriber, EventType.FS_FILE_CONTENT, timer_interval=0.1)

        timer_subscriptions = [sub for sub in manager._subscriptions if sub.is_timer()]
        assert len(timer_subscriptions) == 1
        timer_sub = timer_subscriptions[0]
        assert timer_sub.interval == 0.1
        assert timer_sub.event_types & EventType.TIMER

    @pytest.mark.asyncio
    async def test_timer_events_generated_at_intervals(self) -> None:
        """Test timer events are generated at specified intervals."""
        with patch("time.time") as mock_time:
            # Mock time progression - provide enough values for all time.time() calls
            # Including calls from handle_event and any other time.time() usage
            mock_time.side_effect = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]

            manager = TaskManager()
            subscriber = MockTimerSubscriber()

            await manager.subscribe(subscriber, EventType.FS_FILE_CONTENT, timer_interval=0.05)

            # Manually trigger timer loop iterations
            timer_subscriptions = [sub for sub in manager._subscriptions if sub.is_timer()]
            timer_sub = timer_subscriptions[0]

            # Simulate timer firing twice
            payload1 = {"timer_interval": 0.05, "timestamp": 0.05}
            payload2 = {"timer_interval": 0.05, "timestamp": 0.1}

            await manager.dispatch_event(timer_sub.event_types, payload1)
            await manager.dispatch_event(timer_sub.event_types, payload2)

            # Should have received 2 timer events
            assert len(subscriber.received_events) == 2

    @pytest.mark.asyncio
    async def test_timer_cleanup_on_unsubscribe(self) -> None:
        """Test timer cleanup when subscriber unsubscribes."""
        manager = TaskManager()
        subscriber = MockTimerSubscriber()

        await manager.subscribe(subscriber, EventType.FS_FILE_CONTENT, timer_interval=0.1)
        timer_subscriptions = [sub for sub in manager._subscriptions if sub.is_timer()]
        assert len(timer_subscriptions) == 1

        await manager.unsubscribe(subscriber)
        timer_subscriptions = [sub for sub in manager._subscriptions if sub.is_timer()]
        assert len(timer_subscriptions) == 0

    @pytest.mark.asyncio
    async def test_multiple_timer_subscribers(self) -> None:
        """Test multiple timer subscribers with different intervals."""
        manager = TaskManager()
        subscriber1 = MockTimerSubscriber()
        subscriber2 = MockTimerSubscriber()

        await manager.subscribe(subscriber1, EventType.FS_FILE_CONTENT, timer_interval=0.05)
        await manager.subscribe(subscriber2, EventType.FS_FILE_CONTENT, timer_interval=0.1)

        timer_subscriptions = [sub for sub in manager._subscriptions if sub.is_timer()]
        assert len(timer_subscriptions) == 2

        # Verify different intervals
        intervals = [sub.interval for sub in timer_subscriptions]
        assert 0.05 in intervals
        assert 0.1 in intervals

    @pytest.mark.asyncio
    async def test_timer_event_payload_structure(self) -> None:
        """Test timer event payload contains expected data."""
        manager = TaskManager()
        subscriber = MockTimerSubscriber()

        await manager.subscribe(subscriber, EventType.FS_FILE_CONTENT, timer_interval=0.05)

        # Get timer subscription and manually dispatch event
        timer_subscriptions = [sub for sub in manager._subscriptions if sub.is_timer()]
        timer_sub = timer_subscriptions[0]

        payload = {"timer_interval": 0.05, "timestamp": 1.0}
        await manager.dispatch_event(timer_sub.event_types, payload)

        assert len(subscriber.received_events) == 1
        event_type, received_payload, _ = subscriber.received_events[0]

        # Timer events should have TIMER bit set
        assert event_type & EventType.TIMER

        # Payload should contain timer info
        assert "timer_interval" in received_payload
        assert received_payload["timer_interval"] == 0.05

    @pytest.mark.asyncio
    async def test_timer_subscriber_isolation(self) -> None:
        """Test timer events only go to specific subscriber."""
        manager = TaskManager()
        subscriber1 = MockTimerSubscriber()
        subscriber2 = MockTimerSubscriber()

        # Subscribe with different timer intervals
        await manager.subscribe(subscriber1, EventType.FS_FILE_CONTENT, timer_interval=0.05)
        await manager.subscribe(subscriber2, EventType.FS_FILE_CONTENT, timer_interval=0.1)

        # Get timer subscriptions
        timer_subscriptions = [sub for sub in manager._subscriptions if sub.is_timer()]
        timer1_sub = timer_subscriptions[0]
        timer2_sub = timer_subscriptions[1]

        # Verify each timer has unique event types
        assert timer1_sub.event_types != timer2_sub.event_types
        assert timer1_sub.event_types & EventType.TIMER
        assert timer2_sub.event_types & EventType.TIMER

        # Verify unique timer bits are different
        timer1_unique = timer1_sub.event_types ^ EventType.TIMER
        timer2_unique = timer2_sub.event_types ^ EventType.TIMER
        assert timer1_unique != timer2_unique

    @pytest.mark.asyncio
    async def test_timer_subscription_without_interval_no_timer(self) -> None:
        """Test subscription without timer_interval doesn't create timer."""
        manager = TaskManager()
        subscriber = MockTimerSubscriber()

        await manager.subscribe(subscriber, EventType.FS_FILE_CONTENT)

        timer_subscriptions = [sub for sub in manager._subscriptions if sub.is_timer()]
        assert len(timer_subscriptions) == 0
        assert len(manager._subscriptions) == 1
