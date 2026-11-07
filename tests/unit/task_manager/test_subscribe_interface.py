"""Behavioural coverage for event subscription and removal."""

import pytest

from mcp_guide.task_manager import EventType
from mcp_guide.task_manager.manager import EventResult


class Subscriber:
    def __init__(self, name):
        self.name = name
        self.received_events = []

    def get_name(self):
        return self.name

    async def handle_event(self, event_type, data):
        self.received_events.append((event_type, data))
        return EventResult(result=True)


@pytest.mark.anyio
async def test_subscription_routes_matching_events_and_unsubscribes_only_its_owner(task_manager):
    first = Subscriber("first")
    second = Subscriber("second")
    events = EventType.FS_FILE_CONTENT | EventType.FS_DIRECTORY
    task_manager.subscribe(first, events)
    task_manager.subscribe(first, events)
    task_manager.subscribe(second, EventType.FS_FILE_CONTENT)
    payload = {"path": "docs", "content": "content"}

    await task_manager.dispatch_event(EventType.FS_COMMAND, payload)
    assert first.received_events == second.received_events == []
    await task_manager.dispatch_event(EventType.FS_FILE_CONTENT, payload)
    await task_manager.dispatch_event(EventType.FS_DIRECTORY, payload)
    assert first.received_events == [(EventType.FS_FILE_CONTENT, payload), (EventType.FS_DIRECTORY, payload)]
    assert second.received_events == [(EventType.FS_FILE_CONTENT, payload)]

    task_manager.subscribe(first, EventType.TIMER, timer_interval=1)
    await task_manager.unsubscribe(first)
    assert task_manager.get_subscription_count() == 1
    await task_manager.dispatch_event(EventType.FS_FILE_CONTENT, payload)
    assert len(first.received_events) == 2
    assert second.received_events == [(EventType.FS_FILE_CONTENT, payload)] * 2
    await task_manager.unsubscribe(second)
    assert task_manager.get_subscription_count() == 0


@pytest.mark.parametrize("interval", [0, -1], ids=["zero", "negative"])
def test_subscribe_rejects_nonpositive_timer_interval(task_manager, interval):
    with pytest.raises(ValueError, match="Timer interval must be positive"):
        task_manager.subscribe(Subscriber("invalid"), EventType.TIMER, timer_interval=interval)
    assert task_manager.get_subscription_count() == 0
