"""Task protocol and state definitions."""

from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Protocol

if TYPE_CHECKING:
    from mcp_core.result import Result

    from .interception import FSEventType


class TaskState(Enum):
    """Task states for lifecycle management."""

    IDLE = "idle"
    ACTIVE = "active"
    COMPLETED = "completed"


class TaskType(Enum):
    """Task type classification."""

    ACTIVE = "active"
    SCHEDULED = "scheduled"


class Task(Protocol):
    """Protocol for task implementations."""

    timeout: Optional[float]
    task_type: TaskType

    async def task_start(self) -> tuple[TaskState, Optional[str]]:
        """Start the task."""
        ...

    async def response(self, data: Any) -> tuple[TaskState, Optional[str]]:
        """Handle response data."""
        ...

    async def timeout_expired(self) -> tuple[TaskState, Optional[str]]:
        """Handle timeout expiry."""
        ...

    async def completed(self) -> tuple[TaskState, Optional[str]]:
        """Handle task completion."""
        ...

    async def process_data(self, data_type: "FSEventType", data: dict[str, Any]) -> None:
        """Process agent data and update task state."""
        ...

    async def process_result(self, result: "Result[Any]") -> "Result[Any]":
        """Process result data and return modified result."""
        ...

    async def pause(self) -> None:
        """Pause the task (for scheduled tasks)."""
        ...

    async def resume(self) -> None:
        """Resume the task (for scheduled tasks)."""
        ...
