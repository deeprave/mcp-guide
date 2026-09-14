"""Task manager module for coordinating agent communication."""

from .activation import TaskActivation
from .interception import EventType
from .manager import TaskManager
from .protocol import ProjectTask, TaskSubscriber
from .subscription import Subscription

__all__ = [
    "TaskManager",
    "TaskActivation",
    "EventType",
    "TaskSubscriber",
    "ProjectTask",
    "Subscription",
]
