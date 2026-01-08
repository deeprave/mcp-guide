"""Task manager module for coordinating agent communication."""

from .interception import FSEventType, InterestRegistration
from .manager import TaskManager, get_task_manager
from .protocol import Task, TaskState, TaskType

__all__ = ["TaskManager", "Task", "TaskState", "TaskType", "FSEventType", "InterestRegistration", "get_task_manager"]
