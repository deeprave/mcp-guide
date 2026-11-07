"""Tests for Subscription data structures."""

import time

from mcp_guide.task_manager import EventType
from mcp_guide.task_manager.subscription import Subscription


class MockSubscriber:
    """Mock subscriber for testing."""

    def __init__(self, name: str = "test"):
        self.name = name


def test_timer_subscription_next_fire_time():
    """Test timer subscription calculates next fire time correctly."""
    subscriber = MockSubscriber()

    interval = 2.0

    start_time = time.time()
    sub = Subscription(subscriber, EventType.TIMER, interval)

    # Next fire time should be approximately start_time + interval
    expected_fire_time = start_time + interval
    assert sub.next_fire_time is not None
    assert abs(sub.next_fire_time - expected_fire_time) < 0.1
