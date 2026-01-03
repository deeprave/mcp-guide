"""TaskManager for coordinating agent communication."""

import asyncio
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from .interception import DataType, InterestRegistration
from .protocol import Task, TaskState, TaskType

if TYPE_CHECKING:
    from mcp_core.result import Result


class TaskManager:
    """Generic task coordination system."""

    def __init__(self) -> None:
        """Initialize TaskManager."""
        self._timeout_tasks: Dict[Task, asyncio.Task[None]] = {}
        self._registrations: List[InterestRegistration] = []
        self._pending_instructions: List[str] = []
        self._active_task: Optional[Task] = None
        self._scheduled_tasks: List[Task] = []

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

    def register_interest(
        self, task: Task, flags: DataType, callback: Callable[[DataType, dict[str, Any]], bool]
    ) -> None:
        """Register ephemeral interest in agent data types."""
        registration = InterestRegistration(task=task, flags=flags, callback=callback)
        self._registrations.append(registration)

    async def handle_agent_data(self, data_type: DataType, data: dict[str, Any]) -> dict[str, str]:
        """Handle agent data with task interception."""
        interested_tasks = []

        for registration in self._registrations:
            # Fast bit-flag check first
            if not (registration.flags & data_type):
                continue
            # Only then call expensive callback
            if registration.callback(data_type, data):
                interested_tasks.append(registration.task)

        if not interested_tasks:
            return {"status": "acknowledged"}  # No caching

        # Process with interested tasks and expire registrations
        for task in interested_tasks:
            await task.process_data(data_type, data)
            self._expire_registration(task)

        return {"status": "processed"}

    def _expire_registration(self, task: Task) -> None:
        """Expire registration after handling."""
        self._registrations = [r for r in self._registrations if r.task != task]

    def queue_instruction(self, instruction: str) -> None:
        """Queue an instruction to be added to the next MCP response."""
        self._pending_instructions.append(instruction)

    def process_result(self, result: "Result[Any]") -> "Result[Any]":
        """Process MCP Result and inject any pending instructions."""
        if not self._pending_instructions:
            return result

        # Get the next pending instruction
        instruction = self._pending_instructions.pop(0)

        # Create new result with additional instruction
        from mcp_core.result import Result

        return Result(
            success=result.success,
            value=result.value,
            error=result.error,
            error_type=result.error_type,
            message=result.message,
            arguments=result.arguments,
            instruction=result.instruction,
            additional_instruction=instruction,
            error_data=result.error_data,
        )

    async def _handle_timeout_for_task(self, delay: float, task: Task) -> None:
        """Handle task timeout with state management."""
        try:
            await asyncio.sleep(delay)
            state, instruction = await task.timeout_expired()
            await self._process_task_state_change(task, state, instruction)
        except asyncio.CancelledError:
            pass  # Task completed before timeout

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
