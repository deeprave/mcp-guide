"""TaskManager for coordinating agent communication."""

import asyncio
import contextlib
import threading
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from mcp_core.mcp_log import get_logger

from .interception import EventType
from .protocol import Task, TaskState, TaskSubscriber, TaskType
from .subscription import Subscription

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

        self._pending_instructions: List[str] = []
        self._active_task: Optional[Task] = None
        self._scheduled_tasks: List[Task] = []
        self._cache: Dict[str, Any] = {}  # Keyed storage for task data

        # New pub/sub system
        self._subscriptions: List[Subscription] = []
        self._next_timer_bit = 131072  # Start unique timer bits at 2^17
        self._timer_task: Optional[asyncio.Task[None]] = None

    @classmethod
    def _reset_for_testing(cls) -> None:
        """Reset singleton for testing. DO NOT USE IN PRODUCTION."""
        cls._instance = None
        cls._initialized = False

    async def subscribe(
        self,
        subscriber: TaskSubscriber,
        event_types: EventType,
        timer_interval: Optional[float] = None,
    ) -> None:
        """Subscribe to events with optional timer support."""
        # Parameter validation
        if timer_interval is not None and timer_interval <= 0:
            raise ValueError("Timer interval must be positive")

        # Create appropriate subscription type
        if timer_interval is not None:
            # Always assign unique timer bit for internal tracking
            unique_timer_bit = self._next_timer_bit
            self._next_timer_bit <<= 1  # Next power of 2

            # Create unique timer EventType (TIMER + unique bit)
            unique_timer_event = EventType.TIMER | unique_timer_bit

            subscription = Subscription(subscriber, unique_timer_event, timer_interval)
            subscription.original_event_types = event_types
            subscription.unique_timer_bit = unique_timer_bit

            self._subscriptions.append(subscription)

            # Start timer task immediately
            if self._timer_task is None or self._timer_task.done():
                self._timer_task = asyncio.create_task(self._timer_loop())
        else:
            regular_subscription = Subscription(subscriber, event_types)
            self._subscriptions.append(regular_subscription)

    async def unsubscribe(self, subscriber: TaskSubscriber) -> None:
        """Remove all subscriptions for a subscriber."""
        # Remove all subscriptions for this subscriber
        self._subscriptions = [sub for sub in self._subscriptions if sub.subscriber_ref() is not subscriber]

        # Check if any timer subscriptions remain
        has_timers = any(sub.is_timer() for sub in self._subscriptions)

        # Stop timer task if no timer subscriptions remain
        if not has_timers and self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
            try:
                await self._timer_task
            except asyncio.CancelledError:
                pass
            self._timer_task = None

    async def cleanup(self) -> None:
        """Clean up resources and cancel running tasks."""
        # Cancel timer task if running
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
            try:
                await self._timer_task
            except asyncio.CancelledError:
                pass
            self._timer_task = None

        # Cancel timeout tasks
        for timeout_task in self._timeout_tasks.values():
            timeout_task.cancel()
        self._timeout_tasks.clear()

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

    async def find_task_by_type(self, task_type: type) -> Optional[Task]:
        """Find active or scheduled task by type."""
        all_tasks = ([self._active_task] if self._active_task else []) + self._scheduled_tasks
        for task in all_tasks:
            if isinstance(task, task_type):
                return task
        return None

    async def complete_task(self, task: Task) -> None:
        """Complete a task and cancel its timeout."""
        if task == self._active_task:
            self._active_task = None
            # Resume scheduled tasks when active task completes
            await self._resume_scheduled_tasks()
        elif task in self._scheduled_tasks:
            self._scheduled_tasks.remove(task)

        if task in self._timeout_tasks:
            self._timeout_tasks[task].cancel()
            try:
                await self._timeout_tasks[task]
            except asyncio.CancelledError:
                pass
            del self._timeout_tasks[task]

    async def _process_task_state_change(self, task: Task, new_state: TaskState, instruction: Optional[str]) -> None:
        """Process task state changes and manage lifecycle."""
        if instruction:
            await self.queue_instruction(instruction)

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
            await self.queue_instruction(instruction)

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

    async def dispatch_event(self, data_type: EventType, data: "Union[dict[str, Any], Result[Any]]") -> dict[str, str]:
        """Handle agent data with task interception."""

        # Extract dict from Result if needed
        actual_data: dict[str, Any]
        if hasattr(data, "value") and hasattr(data, "success"):
            # It's a Result object
            result_data = data.value if data.success else {}
            actual_data = result_data if isinstance(result_data, dict) else {}
        else:
            # It's already a dict
            actual_data = data if isinstance(data, dict) else {}

        # Check regular subscriptions
        processed_count = 0
        for subscription in self._subscriptions:
            # Fast bit-flag check first
            if not (subscription.event_types & data_type):
                continue

            # Use handle_event to determine interest and process
            subscriber = subscription.subscriber_ref()
            if subscriber and await subscriber.handle_event(data_type, actual_data):
                processed_count += 1

        if processed_count == 0:
            return {"status": "acknowledged"}

        return {"status": "processed"}

    async def queue_instruction(self, instruction: str) -> None:
        """Queue an instruction to be added to the next MCP response."""
        # Prevent duplicate instructions in the queue
        if instruction not in self._pending_instructions:
            self._pending_instructions.append(instruction)

    async def process_result(self, result: "Result[Any]", event_type: Optional[EventType] = None) -> "Result[Any]":
        """Process MCP Result and delegate to registered tasks."""
        # Handle filesystem events through registered tasks
        if event_type is not None:
            await self.dispatch_event(event_type, result)

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

    async def _timer_loop(self) -> None:
        """Main timer event loop - runs only while there are active timers."""
        import time

        while True:
            # Get timer subscriptions
            timer_subscriptions = [sub for sub in self._subscriptions if sub.is_timer()]

            if not timer_subscriptions:
                # No active timers, exit the loop
                break

            current_time = time.time()
            next_fire_time = float("inf")

            # Check each timer subscription
            for timer_sub in timer_subscriptions[:]:  # Copy to avoid modification during iteration
                subscriber = timer_sub.subscriber_ref()
                if subscriber is None:
                    # Dead subscriber, remove it
                    self._subscriptions.remove(timer_sub)
                    continue

                if timer_sub.next_fire_time is not None and current_time >= timer_sub.next_fire_time:
                    # Fire timer event through regular dispatch mechanism
                    payload = {"timer_interval": timer_sub.interval, "timestamp": current_time}

                    # Dispatch timer event using the same mechanism as regular events
                    await self.dispatch_event(timer_sub.event_types, payload)

                    # Recalculate next fire time
                    timer_sub.update_next_fire_time()

                # Track next fire time
                if timer_sub.next_fire_time is not None:
                    next_fire_time = min(next_fire_time, timer_sub.next_fire_time)

            # Sleep until next timer or short interval
            if next_fire_time != float("inf"):
                sleep_time = max(0.001, next_fire_time - current_time)
                await asyncio.sleep(min(sleep_time, 0.01))  # Cap at 10ms for responsiveness
            else:
                await asyncio.sleep(0.01)


def get_task_manager() -> TaskManager:
    """Get the singleton TaskManager instance."""
    return TaskManager()
