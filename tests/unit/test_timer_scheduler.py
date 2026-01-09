"""Tests for timer event scheduling system."""

import asyncio
import time
from typing import Any

import pytest

from mcp_guide.task_manager import EventType, TaskManager


class MockTimerSubscriber:
    """Mock subscriber for timer events."""

    def __init__(self) -> None:
        self.received_events: list[tuple[EventType, dict[str, Any], float]] = []

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> bool:
        """Handle timer events and record timestamp."""
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
        manager = TaskManager()
        subscriber = MockTimerSubscriber()

        await manager.subscribe(subscriber, EventType.FS_FILE_CONTENT, timer_interval=0.05)

        # Start timer loop
        timer_task = asyncio.create_task(manager._timer_loop())

        try:
            # Wait for multiple timer events
            await asyncio.sleep(0.15)

            # Should have received 2-3 timer events
            assert len(subscriber.received_events) >= 2

            # Check intervals are approximately correct
            if len(subscriber.received_events) >= 2:
                time_diff = subscriber.received_events[1][2] - subscriber.received_events[0][2]
                assert 0.04 <= time_diff <= 0.07  # Allow some timing variance

        finally:
            timer_task.cancel()
            try:
                await timer_task
            except asyncio.CancelledError:
                pass

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

        timer_task = asyncio.create_task(manager._timer_loop())

        try:
            await asyncio.sleep(0.08)

            assert len(subscriber.received_events) >= 1
            event_type, payload, _ = subscriber.received_events[0]

            # Timer events should have TIMER bit set
            assert event_type & EventType.TIMER

            # Payload should contain timer info
            assert "timer_interval" in payload
            assert payload["timer_interval"] == 0.05

        finally:
            timer_task.cancel()
            try:
                await timer_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_timer_subscriber_isolation(self) -> None:
        """Test timer events only go to specific subscriber."""
        manager = TaskManager()
        subscriber1 = MockTimerSubscriber()
        subscriber2 = MockTimerSubscriber()

        # Subscribe with different timer intervals
        await manager.subscribe(subscriber1, EventType.FS_FILE_CONTENT, timer_interval=0.05)
        await manager.subscribe(subscriber2, EventType.FS_FILE_CONTENT, timer_interval=0.1)

        timer_task = asyncio.create_task(manager._timer_loop())

        try:
            await asyncio.sleep(0.12)

            # Both should have received events, subscriber1 should have more or equal
            assert len(subscriber1.received_events) >= 2
            assert len(subscriber2.received_events) >= 1
            # Allow for timing variance - subscriber1 should have at least as many events
            assert len(subscriber1.received_events) >= len(subscriber2.received_events)

        finally:
            timer_task.cancel()
            try:
                await timer_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_timer_subscription_without_interval_no_timer(self) -> None:
        """Test subscription without timer_interval doesn't create timer."""
        manager = TaskManager()
        subscriber = MockTimerSubscriber()

        await manager.subscribe(subscriber, EventType.FS_FILE_CONTENT)

        timer_subscriptions = [sub for sub in manager._subscriptions if sub.is_timer()]
        assert len(timer_subscriptions) == 0
        assert len(manager._subscriptions) == 1
