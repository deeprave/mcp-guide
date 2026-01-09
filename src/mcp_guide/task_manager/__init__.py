"""Task manager module for coordinating agent communication."""

from .interception import EventType
from .manager import TaskManager, get_task_manager
from .protocol import TaskSubscriber
from .subscription import Subscription

__all__ = [
    "TaskManager",
    "EventType",
    "TaskSubscriber",
    "Subscription",
    "get_task_manager",
]
