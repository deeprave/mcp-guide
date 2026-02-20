"""Tests for subscribe/unsubscribe interface."""

import pytest

from mcp_guide.task_manager import EventType


class MockSubscriber:
    """Mock subscriber for testing."""

    def __init__(self, name: str = "test"):
        self.name = name
        self.received_events = []

    def get_name(self) -> str:
        """Get subscriber name."""
        return self.name

    async def handle_event(self, event_type: EventType, data: dict) -> bool:
        """Handle events and record them."""
        self.received_events.append((event_type, data))
        return True


@pytest.mark.asyncio
async def test_subscribe_basic(task_manager):
    """Test basic event subscription."""
    subscriber = MockSubscriber()

    task_manager.subscribe(subscriber, EventType.FS_FILE_CONTENT)

    assert len(task_manager._subscriptions) == 1
    subscription = task_manager._subscriptions[0]
    assert subscription.subscriber is subscriber
    assert subscription.event_types == EventType.FS_FILE_CONTENT


@pytest.mark.asyncio
async def test_subscribe_multiple_event_types(task_manager):
    """Test subscription with multiple EventTypes."""
    subscriber = MockSubscriber()

    event_types = EventType.FS_FILE_CONTENT | EventType.FS_DIRECTORY

    task_manager.subscribe(subscriber, event_types)

    assert len(task_manager._subscriptions) == 1
    subscription = task_manager._subscriptions[0]
    assert subscription.event_types == event_types


@pytest.mark.asyncio
async def test_subscribe_timer_event(task_manager):
    """Test timer event subscription."""
    subscriber = MockSubscriber()

    task_manager.subscribe(subscriber, EventType.TIMER, timer_interval=1.0)

    timer_subscriptions = [sub for sub in task_manager._subscriptions if sub.is_timer()]
    assert len(timer_subscriptions) == 1
    timer_sub = timer_subscriptions[0]
    assert timer_sub.subscriber is subscriber
    assert timer_sub.event_types & EventType.TIMER
    assert timer_sub.interval == 1.0


@pytest.mark.asyncio
async def test_subscribe_timer_with_other_events(task_manager):
    """Test timer subscription with additional event types."""
    subscriber = MockSubscriber()

    event_types = EventType.TIMER | EventType.FS_FILE_CONTENT

    task_manager.subscribe(subscriber, event_types, timer_interval=0.5)

    timer_subscriptions = [sub for sub in task_manager._subscriptions if sub.is_timer()]
    assert len(timer_subscriptions) == 1
    timer_sub = timer_subscriptions[0]
    assert timer_sub.original_event_types == event_types
    assert timer_sub.interval == 0.5


@pytest.mark.asyncio
async def test_subscribe_multiple_subscribers(task_manager):
    """Test multiple subscribers for same event type."""
    subscriber1 = MockSubscriber("sub1")
    subscriber2 = MockSubscriber("sub2")

    task_manager.subscribe(subscriber1, EventType.FS_FILE_CONTENT)
    task_manager.subscribe(subscriber2, EventType.FS_FILE_CONTENT)

    assert len(task_manager._subscriptions) == 2


@pytest.mark.asyncio
async def test_unsubscribe_all(task_manager):
    """Test unsubscribe removes all subscriptions for subscriber."""
    subscriber = MockSubscriber()

    # Subscribe to multiple events
    task_manager.subscribe(subscriber, EventType.FS_FILE_CONTENT)
    task_manager.subscribe(subscriber, EventType.FS_DIRECTORY)
    task_manager.subscribe(subscriber, EventType.TIMER, timer_interval=1.0)

    assert len(task_manager._subscriptions) == 3

    # Unsubscribe should remove all
    await task_manager.unsubscribe(subscriber)

    assert len(task_manager._subscriptions) == 0


@pytest.mark.asyncio
async def test_unsubscribe_specific_subscriber(task_manager):
    """Test unsubscribe only removes subscriptions for specific subscriber."""
    subscriber1 = MockSubscriber("sub1")
    subscriber2 = MockSubscriber("sub2")

    task_manager.subscribe(subscriber1, EventType.FS_FILE_CONTENT)
    task_manager.subscribe(subscriber2, EventType.FS_FILE_CONTENT)

    assert len(task_manager._subscriptions) == 2

    # Unsubscribe only subscriber1
    await task_manager.unsubscribe(subscriber1)

    assert len(task_manager._subscriptions) == 1
    remaining_sub = task_manager._subscriptions[0]
    assert remaining_sub.subscriber is subscriber2


@pytest.mark.asyncio
async def test_subscribe_weak_reference_cleanup(task_manager):
    """Test strong reference behavior (changed from weak references)."""
    subscriber = MockSubscriber()

    task_manager.subscribe(subscriber, EventType.FS_FILE_CONTENT)
    assert len(task_manager._subscriptions) == 1

    # Store subscriber id before deletion
    subscriber_id = id(subscriber)

    # Delete subscriber - strong reference keeps it alive
    del subscriber

    # Subscription still exists and keeps subscriber alive
    assert len(task_manager._subscriptions) == 1
    assert task_manager._subscriptions[0].subscriber is not None
    assert id(task_manager._subscriptions[0].subscriber) == subscriber_id


@pytest.mark.asyncio
async def test_subscribe_auto_timer_event_type(task_manager):
    """Test automatic timer event type assignment when not provided."""
    subscriber = MockSubscriber()

    # Subscribe with timer interval but no timer event type
    task_manager.subscribe(subscriber, EventType.FS_FILE_CONTENT, timer_interval=1.0)

    timer_subscriptions = [sub for sub in task_manager._subscriptions if sub.is_timer()]
    assert len(timer_subscriptions) == 1
    timer_sub = timer_subscriptions[0]
    # Should automatically add TIMER bit
    assert timer_sub.event_types & EventType.TIMER
    # Original event types should be preserved separately
    assert hasattr(timer_sub, "original_event_types")
    assert timer_sub.original_event_types & EventType.FS_FILE_CONTENT


@pytest.mark.asyncio
async def test_subscribe_parameter_validation(task_manager):
    """Test parameter validation for subscribe method."""
    subscriber = MockSubscriber()

    # Invalid timer interval
    with pytest.raises(ValueError, match="Timer interval must be positive"):
        task_manager.subscribe(subscriber, EventType.TIMER, timer_interval=0)

    with pytest.raises(ValueError, match="Timer interval must be positive"):
        task_manager.subscribe(subscriber, EventType.TIMER, timer_interval=-1.0)


@pytest.mark.asyncio
async def test_unique_timer_event_assignment(task_manager):
    """Test each timer subscription gets unique EventType."""
    subscriber1 = MockSubscriber("sub1")
    subscriber2 = MockSubscriber("sub2")

    task_manager.subscribe(subscriber1, EventType.FS_FILE_CONTENT, timer_interval=1.0)
    task_manager.subscribe(subscriber2, EventType.FS_FILE_CONTENT, timer_interval=2.0)

    timer_subscriptions = [sub for sub in task_manager._subscriptions if sub.is_timer()]
    timer1_event = timer_subscriptions[0].event_types
    timer2_event = timer_subscriptions[1].event_types

    # Both should have TIMER bit
    assert timer1_event & EventType.TIMER
    assert timer2_event & EventType.TIMER

    # But should have different unique bits (starting at 2^17)
    assert timer1_event != timer2_event
    assert timer1_event & 131072  # First unique bit (2^17)
    assert timer2_event & 262144  # Second unique bit (2^18)


@pytest.mark.asyncio
async def test_timer_bit_allocation_starts_at_2_16(task_manager):
    """Test timer unique bits start at 2^17 (131072)."""
    subscriber = MockSubscriber()

    task_manager.subscribe(subscriber, EventType.FS_FILE_CONTENT, timer_interval=1.0)

    timer_subscriptions = [sub for sub in task_manager._subscriptions if sub.is_timer()]
    timer_event = timer_subscriptions[0].event_types

    # The timer event includes: original events + unique timer bit (no TIMER flag added)
    # For FS_FILE_CONTENT (1) + unique bit (131072) = 131073
    unique_bits = timer_event.value - EventType.FS_FILE_CONTENT.value  # Extract unique timer bit

    assert unique_bits >= 131072  # Must be 2^17 or higher


@pytest.mark.asyncio
async def test_timer_original_event_types_preserved(task_manager):
    """Test original event_types are preserved for filtering."""
    subscriber = MockSubscriber()

    original_events = EventType.FS_FILE_CONTENT | EventType.FS_DIRECTORY

    task_manager.subscribe(subscriber, original_events, timer_interval=1.0)

    timer_subscriptions = [sub for sub in task_manager._subscriptions if sub.is_timer()]
    timer_sub = timer_subscriptions[0]
    assert hasattr(timer_sub, "original_event_types")
    assert timer_sub.original_event_types == original_events


@pytest.mark.asyncio
async def test_multiple_timer_unique_assignment(task_manager):
    """Test multiple timers get sequential unique bits."""

    # Create 3 timer subscriptions
    for i in range(3):
        subscriber = MockSubscriber(f"sub{i}")
        task_manager.subscribe(subscriber, EventType.FS_FILE_CONTENT, timer_interval=1.0)

    # Check they get sequential counter values shifted left by 17
    # Counter starts at 1: (1 << 17), (2 << 17), (3 << 17)
    expected_bits = [131072, 262144, 393216]  # 1<<17, 2<<17, 3<<17

    timer_subscriptions = [sub for sub in task_manager._subscriptions if sub.is_timer()]
    for i, expected_bit in enumerate(expected_bits):
        timer_event = timer_subscriptions[i].event_types
        # Extract unique timer bit by subtracting base events and TIMER flag
        unique_bits = timer_event.value - EventType.FS_FILE_CONTENT.value - EventType.TIMER.value
        assert unique_bits == expected_bit
