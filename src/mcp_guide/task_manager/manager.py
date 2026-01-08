"""TaskManager for coordinating agent communication."""

import asyncio
import contextlib
import threading
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from mcp_core.mcp_log import get_logger

from .interception import FSEventType, InterestRegistration
from .protocol import Task, TaskState, TaskType

if TYPE_CHECKING:
    from mcp_core.result import Result

logger = get_logger(__name__)


class TaskManager:
    """Generic task coordination system."""

    _instance: Optional["TaskManager"] = None
    _initialized: bool = False
    _lock = threading.Lock()

    def __new__(cls) -> "TaskManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize TaskManager."""
        if self._initialized:
            return
        self._initialized = True
        self._timeout_tasks: Dict[Task, asyncio.Task[None]] = {}
        self._registrations: List[InterestRegistration] = []
        self._pending_instructions: List[str] = []
        self._active_task: Optional[Task] = None
        self._scheduled_tasks: List[Task] = []
        self._cache: Dict[str, Any] = {}  # Keyed storage for task data

    @classmethod
    def _reset_for_testing(cls) -> None:
        """Reset singleton for testing. DO NOT USE IN PRODUCTION."""
        cls._instance = None
        cls._initialized = False

    async def register_task(self, task: Task) -> None:
        """Register and start a task."""
        # Enforce single active task constraint
        if task.task_type == TaskType.ACTIVE and self._active_task is not None:
            raise RuntimeError("Cannot register task: another task is already active")

        state, instruction = await task.task_start()
        await self._process_task_state_change(task, state, instruction)

        if task.timeout and task.timeout > 0:
            timeout_task = asyncio.create_task(self._handle_timeout_for_task(task.timeout, task))
            self._timeout_tasks[task] = timeout_task

    def find_task_by_type(self, task_type: type) -> Optional[Task]:
        """Find active or scheduled task by type."""
        all_tasks = ([self._active_task] if self._active_task else []) + self._scheduled_tasks
        for task in all_tasks:
            if isinstance(task, task_type):
                return task
        return None

    def complete_task(self, task: Task) -> None:
        """Complete a task and cancel its timeout."""
        if task == self._active_task:
            self._active_task = None
            # Resume scheduled tasks when active task completes
            asyncio.create_task(self._resume_scheduled_tasks())
        elif task in self._scheduled_tasks:
            self._scheduled_tasks.remove(task)

        if task in self._timeout_tasks:
            self._timeout_tasks[task].cancel()
            del self._timeout_tasks[task]

    async def _process_task_state_change(self, task: Task, new_state: TaskState, instruction: Optional[str]) -> None:
        """Process task state changes and manage lifecycle."""
        if instruction:
            self.queue_instruction(instruction)

        if new_state == TaskState.ACTIVE:
            if task.task_type == TaskType.ACTIVE:
                self._active_task = task
                await self._pause_scheduled_tasks()
            elif task.task_type == TaskType.SCHEDULED:
                if task not in self._scheduled_tasks:
                    self._scheduled_tasks.append(task)
        elif new_state == TaskState.COMPLETED:
            await self._handle_task_completion(task)
        elif new_state == TaskState.IDLE:
            # Task returned to idle state
            if task == self._active_task:
                self._active_task = None
                await self._resume_scheduled_tasks()

    async def _handle_task_completion(self, task: Task) -> None:
        """Handle task completion."""
        state, instruction = await task.completed()
        if instruction:
            self.queue_instruction(instruction)

        # Process the completion state
        if state == TaskState.IDLE:
            if task == self._active_task:
                self._active_task = None
                await self._resume_scheduled_tasks()
            elif task in self._scheduled_tasks:
                self._scheduled_tasks.remove(task)
        elif state == TaskState.COMPLETED:
            # Handle COMPLETED state same as IDLE for task cleanup
            if task == self._active_task:
                self._active_task = None
                await self._resume_scheduled_tasks()
            elif task in self._scheduled_tasks:
                self._scheduled_tasks.remove(task)

    def register_interest(
        self, task: Task, flags: FSEventType, callback: Callable[[FSEventType, dict[str, Any]], bool]
    ) -> None:
        """Register ephemeral interest in agent data types."""
        registration = InterestRegistration(task=task, flags=flags, callback=callback)
        self._registrations.append(registration)

    async def handle_agent_data(
        self, data_type: FSEventType, data: "Union[dict[str, Any], Result[Any]]"
    ) -> dict[str, str]:
        """Handle agent data with task interception."""
        interested_tasks = []

        # Extract dict from Result if needed
        actual_data: dict[str, Any]
        if hasattr(data, "value") and hasattr(data, "success"):
            # It's a Result object
            result_data = data.value if data.success else {}
            actual_data = result_data if isinstance(result_data, dict) else {}
        else:
            # It's already a dict
            actual_data = data if isinstance(data, dict) else {}

        for registration in self._registrations:
            # Fast bit-flag check first
            if not (registration.flags & data_type):
                continue

            # Use callback to determine interest
            if registration.callback(data_type, actual_data):
                interested_tasks.append(registration.task)

        if not interested_tasks:
            return {"status": "acknowledged"}

        # Process with interested tasks - pass the dict data
        for task in interested_tasks:
            await task.process_data(data_type, actual_data)

        return {"status": "processed"}

    def _expire_registration(self, task: Task) -> None:
        """Expire registration after handling."""
        self._registrations = [r for r in self._registrations if r.task != task]

    def queue_instruction(self, instruction: str) -> None:
        """Queue an instruction to be added to the next MCP response."""
        self._pending_instructions.append(instruction)

    async def process_result(self, result: "Result[Any]", event_type: Optional["FSEventType"] = None) -> "Result[Any]":
        """Process MCP Result and delegate to registered tasks."""
        # Handle filesystem events through registered tasks
        if event_type is not None:
            await self.handle_agent_data(event_type, result)

        # Check for queued instructions from tasks (FIFO)
        if self._pending_instructions:
            # Get the first instruction (FIFO)
            instruction = self._pending_instructions.pop(0)
            from dataclasses import replace

            return replace(result, additional_agent_instructions=instruction)

        return result

    async def _handle_timeout_for_task(self, delay: float, task: Task) -> None:
        """Handle task timeout with state management."""
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.sleep(delay)
            state, instruction = await task.timeout_expired()
            await self._process_task_state_change(task, state, instruction)

    async def handle_task_response(self, task: Task, data: Any) -> None:
        """Handle task response and process state changes."""
        state, instruction = await task.response(data)
        await self._process_task_state_change(task, state, instruction)

    async def _pause_scheduled_tasks(self) -> None:
        """Pause all scheduled tasks."""
        for task in self._scheduled_tasks:
            await task.pause()

    async def _resume_scheduled_tasks(self) -> None:
        """Resume all scheduled tasks."""
        for task in self._scheduled_tasks:
            await task.resume()

    def get_cached_data(self, key: str) -> Any:
        """Get cached data by key."""
        return self._cache.get(key)

    def set_cached_data(self, key: str, value: Any) -> None:
        """Set cached data by key."""
        self._cache[key] = value

    def clear_cached_data(self, key: str) -> None:
        """Clear cached data by key."""
        self._cache.pop(key, None)


def get_task_manager() -> TaskManager:
    """Get the singleton TaskManager instance."""
    return TaskManager()
