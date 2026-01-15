"""Subscription data structures for pub/sub system."""

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from .interception import EventType

if TYPE_CHECKING:
    from .protocol import TaskSubscriber


@dataclass
class Subscription:
    """Subscription to events with strong reference to subscriber."""

    subscriber: "TaskSubscriber"
    event_types: EventType
    interval: Optional[float] = None
    next_fire_time: Optional[float] = field(init=False, default=None)
    original_event_types: Optional[EventType] = None
    unique_timer_bit: Optional[int] = None

    def __init__(self, subscriber: "TaskSubscriber", event_types: EventType, interval: Optional[float] = None):
        """Initialize subscription with strong reference to subscriber."""
        self.event_types = event_types
        self.subscriber = subscriber
        self.interval = interval
        self.next_fire_time = time.time() + interval if interval is not None else None

    def is_timer(self) -> bool:
        """Check if this is a timer subscription."""
        return self.interval is not None

    def update_next_fire_time(self) -> None:
        """Update next fire time for recurring timer."""
        if self.interval is not None:
            self.next_fire_time = time.time() + self.interval
