"""Task manager module for coordinating agent communication."""

from .interception import EventType
from .manager import TaskManager
from .protocol import TaskSubscriber
from .subscription import Subscription

__all__ = [
    "TaskManager",
    "EventType",
    "TaskSubscriber",
    "Subscription",
]
