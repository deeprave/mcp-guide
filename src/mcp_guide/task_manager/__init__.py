"""Task manager module for coordinating agent communication."""

from .interception import EventType
from .manager import TaskManager, get_task_manager
from .protocol import Task, TaskState, TaskSubscriber, TaskType
from .subscription import Subscription

__all__ = [
    "TaskManager",
    "Task",
    "TaskState",
    "TaskType",
    "EventType",
    "TaskSubscriber",
    "Subscription",
    "get_task_manager",
]
