"""TaskManager for coordinating agent communication."""

import asyncio
import threading
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from mcp_core.mcp_log import get_logger

from .interception import EventType
from .protocol import TaskSubscriber
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

        self._pending_instructions: List[str] = []
        self._cache: Dict[str, Any] = {}  # Keyed storage for task data

        # New pub/sub system
        self._subscriptions: List[Subscription] = []
        self._next_timer_bit = 131072  # Start unique timer bits at 2^17
        self._timer_task: Optional[asyncio.Task[None]] = None

        # Task statistics
        self._task_stats: Dict[str, Dict[str, Any]] = {}
        self._peak_task_count = 0
        self._total_timer_runs = 0

    @classmethod
    def _reset_for_testing(cls) -> None:
        """Reset singleton for testing. DO NOT USE IN PRODUCTION."""
        cls._instance = None
        cls._initialized = False

    def _get_subscriber_name(self, subscriber: TaskSubscriber) -> str:
        """Get a readable name for the subscriber."""
        return subscriber.get_name()

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

        subscriber_name = self._get_subscriber_name(subscriber)
        current_time = time.time()

        # Create appropriate subscription type
        if timer_interval is not None:
            # Always assign unique timer bit for internal tracking
            if self._next_timer_bit > (1 << 30):  # Prevent overflow
                raise RuntimeError("Maximum number of concurrent timer subscriptions exceeded")

            unique_timer_bit = self._next_timer_bit
            self._next_timer_bit <<= 1  # Next power of 2

            # Create unique timer EventType (TIMER + unique bit) and combine with original events
            unique_timer_event = EventType.TIMER | unique_timer_bit
            combined_event_types = event_types | unique_timer_event

            subscription = Subscription(subscriber, combined_event_types, timer_interval)
            subscription.original_event_types = event_types
            subscription.unique_timer_bit = unique_timer_bit

            self._subscriptions.append(subscription)

            # Track timer statistics
            task_id = f"{subscriber_name}_{id(subscriber)}"
            self._task_stats[task_id] = {
                "name": subscriber_name,
                "type": "timer",
                "started": current_time,
                "last_data": current_time,
                "interval": timer_interval,
                "last_run": None,
                "next_run": current_time + timer_interval,
                "run_count": 0,
            }

            # Start timer task immediately
            if self._timer_task is None or self._timer_task.done():
                self._timer_task = asyncio.create_task(self._timer_loop())
        else:
            regular_subscription = Subscription(subscriber, event_types)
            self._subscriptions.append(regular_subscription)

            # Track regular task statistics
            task_id = f"{subscriber_name}_{id(subscriber)}"
            self._task_stats[task_id] = {
                "name": subscriber_name,
                "type": "regular",
                "started": current_time,
                "last_data": None,
            }

        # Update peak count
        self._peak_task_count = max(self._peak_task_count, len(self._subscriptions))

    async def unsubscribe(self, subscriber: TaskSubscriber) -> None:
        """Remove all subscriptions for a subscriber."""
        # Clean up statistics
        subscriber_name = self._get_subscriber_name(subscriber)
        task_id = f"{subscriber_name}_{id(subscriber)}"
        self._task_stats.pop(task_id, None)

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

        logger.trace(f"Dispatching event {data_type} to {len(self._subscriptions)} subscriptions")

        # Check regular subscriptions and clean up dead references
        processed_count = 0
        current_time = time.time()
        active_subscriptions = []

        for subscription in self._subscriptions:
            subscriber = subscription.subscriber_ref()
            if subscriber is None:
                logger.trace("Subscription has dead weak reference, removing")
                continue

            active_subscriptions.append(subscription)
            logger.trace(f"Checking subscription: {subscriber.get_name()} with event_types {subscription.event_types}")
            if subscription.event_types & data_type:
                logger.trace(
                    f"Event {data_type} matches subscription {subscription.event_types}, dispatching to {subscriber.get_name()}"
                )
                try:
                    handled = await subscriber.handle_event(data_type, actual_data)
                    if handled:
                        processed_count += 1
                        logger.trace(f"Event handled by {subscriber.get_name()}")
                    else:
                        logger.trace(f"Event not handled by {subscriber.get_name()}")
                except Exception as e:
                    logger.warning(f"Error handling event in {subscriber.get_name()}: {e}")
            else:
                logger.trace(f"Event {data_type} does not match subscription {subscription.event_types}")

        # Update subscriptions list with only active ones
        self._subscriptions = active_subscriptions

        logger.trace(f"Event {data_type} processed by {processed_count} subscribers")

        # Update statistics for processed subscribers
        for subscription in self._subscriptions:
            if subscription.event_types & data_type:
                subscriber = subscription.subscriber_ref()
                if subscriber:
                    subscriber_name = self._get_subscriber_name(subscriber)
                    task_id = f"{subscriber_name}_{id(subscriber)}"
                    if task_id in self._task_stats:
                        self._task_stats[task_id]["last_data"] = current_time

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

    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task statistics for template context."""
        from mcp_guide.utils.duration_formatter import format_duration

        current_time = time.time()

        running_tasks = []
        timer_tasks = []

        for task_id, stats in self._task_stats.items():
            runtime_seconds = current_time - stats["started"]
            task_info = {
                "name": stats["name"],
                "started": stats["started"],
                "last_data": stats.get("last_data"),
                "runtime": format_duration(runtime_seconds),
            }

            if stats["type"] == "timer":
                last_run_ago = current_time - stats["last_run"] if stats.get("last_run") else None
                next_run_in = stats["next_run"] - current_time if stats.get("next_run") else None

                task_info.update(
                    {
                        "interval": round(stats["interval"], 2),
                        "last_run": stats.get("last_run"),
                        "next_run": stats.get("next_run"),
                        "run_count": stats["run_count"],
                        "time_since_last": format_duration(last_run_ago) if last_run_ago else None,
                        "time_until_next": format_duration(next_run_in) if next_run_in else None,
                    }
                )
                timer_tasks.append(task_info)

            running_tasks.append(task_info)

        return {
            "running": running_tasks,
            "timers": timer_tasks,
            "count": len(self._subscriptions),
            "peak_count": self._peak_task_count,
            "total_timer_runs": self._total_timer_runs,
        }

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

                    # Update timer statistics
                    subscriber_name = self._get_subscriber_name(subscriber)
                    task_id = f"{subscriber_name}_{id(subscriber)}"
                    if task_id in self._task_stats:
                        stats = self._task_stats[task_id]
                        stats["last_run"] = current_time
                        stats["run_count"] += 1
                        self._total_timer_runs += 1

                    # Dispatch timer event using the same mechanism as regular events
                    await self.dispatch_event(timer_sub.event_types, payload)

                    # Recalculate next fire time
                    timer_sub.update_next_fire_time()

                    # Update next run time in statistics
                    if task_id in self._task_stats:
                        self._task_stats[task_id]["next_run"] = timer_sub.next_fire_time

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
