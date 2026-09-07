"""Recurring timers emit real scheduler events and release subscriptions."""

import asyncio
from typing import Any

import pytest

from mcp_guide.task_manager import EventType, TaskManager
from mcp_guide.task_manager.manager import EventResult


class RecordingTimerSubscriber:
    def __init__(self):
        self.events: list[tuple[EventType, dict[str, Any]]] = []
        self.repeated = asyncio.Event()

    def get_name(self) -> str:
        return "RecordingTimerSubscriber"

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult:
        self.events.append((event_type, data))
        if len(self.events) >= 2:
            self.repeated.set()
        return EventResult(result=True)


@pytest.mark.anyio
@pytest.mark.parametrize("interval", [0.01, 0.02], ids=["short-interval", "longer-interval"])
async def test_recurring_timer_delivers_payloads_until_unsubscribed(interval):
    manager = TaskManager()
    subscriber = RecordingTimerSubscriber()
    manager.subscribe(subscriber, EventType.FS_FILE_CONTENT, timer_interval=interval)
    await manager.start()
    try:
        await asyncio.wait_for(subscriber.repeated.wait(), timeout=2)
        await manager.unsubscribe(subscriber)
        assert manager.get_subscription_count() == 0
        assert len(subscriber.events) >= 2
        for event_type, payload in subscriber.events:
            assert event_type & EventType.TIMER
            assert payload["timer_interval"] == interval
        timestamps = [payload["timestamp"] for _, payload in subscriber.events]
        assert all(later > earlier for earlier, later in zip(timestamps, timestamps[1:]))
        delivered = len(subscriber.events)
        await manager.dispatch_event(EventType.TIMER, {"timestamp": timestamps[-1] + interval})
        assert len(subscriber.events) == delivered
    finally:
        await manager.cleanup()
