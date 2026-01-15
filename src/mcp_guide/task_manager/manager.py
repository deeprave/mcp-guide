"""TaskManager for coordinating agent communication."""

import asyncio
import threading
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from mcp_core.mcp_log import get_logger
from mcp_guide.decorators import task_init

from .interception import EventType
from .protocol import TaskSubscriber
from .subscription import Subscription

if TYPE_CHECKING:
    from mcp_core.result import Result

logger = get_logger(__name__)


@task_init
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
        self._next_timer_id = 1  # Simple counter for unique timer IDs
        self._timer_task: Optional[asyncio.Task[None]] = None

        # Task statistics
        self._task_stats: Dict[str, Dict[str, Any]] = {}
        self._peak_task_count = 0
        self._total_timer_runs = 0

        # Register as task manager
        try:
            from mcp_core.tool_decorator import set_task_manager

            set_task_manager(self)
        except ImportError:
            pass  # Gracefully handle missing modules during testing

        # Start timer tasks
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.start())
        except RuntimeError:
            # No loop yet, will start when needed
            pass

    @classmethod
    def _reset_for_testing(cls) -> None:
        """Reset singleton for testing. DO NOT USE IN PRODUCTION."""
        # Clean up existing instance resources before resetting
        if cls._instance is not None:
            # Reset instance state
            cls._instance._next_timer_id = 1
            cls._instance._subscriptions = []
            cls._instance._pending_instructions = []
            cls._instance._cache = {}
            cls._instance._task_stats = {}
            cls._instance._peak_task_count = 0
            cls._instance._total_timer_runs = 0

            import asyncio

            try:
                # Try to clean up in current event loop
                loop = asyncio.get_running_loop()
                loop.create_task(cls._instance.cleanup())
            except RuntimeError:
                # No running event loop, create one temporarily
                asyncio.run(cls._instance.cleanup())

        cls._instance = None
        cls._initialized = False

    def _get_subscriber_name(self, subscriber: TaskSubscriber) -> str:
        """Get a readable name for the subscriber."""
        try:
            return subscriber.get_name()
        except (AttributeError, NotImplementedError):
            # Fallback to default naming if get_name() not properly implemented
            return f"{subscriber.__class__.__name__}_{id(subscriber)}"

    def subscribe(
        self,
        subscriber: TaskSubscriber,
        event_types: EventType,
        timer_interval: Optional[float] = None,
    ) -> None:
        """Subscribe to events with optional timer support."""
        logger.trace(
            f"TaskManager.subscribe: {subscriber.get_name()} subscribing to {event_types}, interval={timer_interval}"
        )

        # Parameter validation
        if timer_interval is not None and timer_interval <= 0:
            raise ValueError("Timer interval must be positive")

        subscriber_name = self._get_subscriber_name(subscriber)
        current_time = time.time()

        # Create appropriate subscription type
        if timer_interval is not None:
            # Assign unique timer bit for tracking
            unique_timer_bit = self._next_timer_id << 17  # Shift above TIMER (2^16)
            self._next_timer_id += 1

            # Add TIMER flag and unique bit to event_types
            combined_event_types = event_types | EventType.TIMER | unique_timer_bit

            subscription = Subscription(subscriber, combined_event_types, timer_interval)
            subscription.original_event_types = event_types
            subscription.unique_timer_bit = unique_timer_bit

            self._subscriptions.append(subscription)
            logger.trace(
                f"TaskManager.subscribe: Added timer subscription for {subscriber_name}, total: {len(self._subscriptions)}"
            )

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

    async def start(self) -> None:
        """Start all timer tasks for subscribed tasks."""
        # Start timer task if any timer subscriptions exist
        has_timer_subscriptions = any(sub.interval is not None for sub in self._subscriptions)

        if has_timer_subscriptions and (self._timer_task is None or self._timer_task.done()):
            self._timer_task = asyncio.create_task(self._timer_loop())

    async def on_tool(self) -> None:
        """Call on_tool for all subscribers after tool/prompt execution."""
        # Ensure timer loop is started
        await self.start()

        logger.trace(f"TaskManager.on_tool called, {len(self._subscriptions)} subscriptions")
        for i, subscription in enumerate(self._subscriptions):
            subscriber = subscription.subscriber
            logger.trace(f"Subscription {i}: subscriber is {subscriber}")
            try:
                subscriber_name = subscriber.get_name()
                logger.trace(f"Calling on_tool for {subscriber_name}")
                await subscriber.on_tool()
                logger.trace(f"Completed on_tool for {subscriber_name}")
            except Exception as e:
                logger.warning(f"Error in on_tool for {subscriber.get_name()}: {e}")

    async def unsubscribe(self, subscriber: TaskSubscriber) -> None:
        """Remove all subscriptions for a subscriber."""
        # Clean up statistics
        subscriber_name = self._get_subscriber_name(subscriber)
        task_id = f"{subscriber_name}_{id(subscriber)}"
        self._task_stats.pop(task_id, None)

        # Remove all subscriptions for this subscriber
        self._subscriptions = [sub for sub in self._subscriptions if sub.subscriber is not subscriber]

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
            subscriber = subscription.subscriber
            if subscriber is None:
                logger.trace("Subscription has dead weak reference, removing")
                continue

            active_subscriptions.append(subscription)
            logger.trace(f"Checking subscription: {subscriber.get_name()} with event_types {subscription.event_types}")
            if subscription.event_types & data_type:
                logger.trace(
                    f"Event {data_type} matches subscription {subscription.event_types}, dispatching to {subscriber.get_name()}"
                )
                handled = False
                try:
                    handled = await subscriber.handle_event(data_type, actual_data)
                    if handled:
                        processed_count += 1
                        logger.trace(f"Event handled by {subscriber.get_name()}")
                    else:
                        logger.trace(f"Event not handled by {subscriber.get_name()}")
                except Exception as e:
                    logger.warning(f"Error handling event in {subscriber.get_name()}: {e}")

                # Check if this was a TIMER_ONCE event that was handled - remove the TIMER_ONCE flag
                if (data_type & EventType.TIMER_ONCE) and (subscription.event_types & EventType.TIMER_ONCE) and handled:
                    logger.trace(f"Removing TIMER_ONCE flag from {subscriber.get_name()}")
                    subscription.event_types &= ~EventType.TIMER_ONCE  # Remove TIMER_ONCE flag
                    subscription.interval = None  # Stop timer from firing again
                    subscription.next_fire_time = None

                    # Update task stats - if no timer flags remain, change to regular task
                    subscriber_name = self._get_subscriber_name(subscriber)
                    task_id = f"{subscriber_name}_{id(subscriber)}"
                    if task_id in self._task_stats:
                        remaining_timer_flags = subscription.event_types & (EventType.TIMER | EventType.TIMER_ONCE)
                        if not remaining_timer_flags:
                            self._task_stats[task_id]["type"] = "regular"
                            self._task_stats[task_id].pop("interval", None)
                            self._task_stats[task_id].pop("last_run", None)
                            self._task_stats[task_id].pop("next_run", None)
                            self._task_stats[task_id].pop("run_count", None)
            else:
                logger.trace(f"Event {data_type} does not match subscription {subscription.event_types}")

        # Update subscriptions list with only active ones
        self._subscriptions = active_subscriptions

        logger.trace(f"Event {data_type} processed by {processed_count} subscribers")

        # Update statistics for processed subscribers
        for subscription in self._subscriptions:
            if subscription.event_types & data_type:
                subscriber = subscription.subscriber
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

        # Check for workflow change content that should replace the main response value
        workflow_change_content = self.get_cached_data("workflow_change_content")
        if workflow_change_content:
            # Clear the cached content after using it
            self.set_cached_data("workflow_change_content", None)
            # Replace the result value with the workflow change content
            from dataclasses import replace

            result = replace(result, value=workflow_change_content)
            # When workflow_change_content is applied, skip pending instructions for this response
            return result

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

                task_info |= {
                    "interval": round(stats["interval"], 2),
                    "last_run": stats.get("last_run"),
                    "next_run": stats.get("next_run"),
                    "run_count": stats["run_count"],
                    "time_since_last": (format_duration(last_run_ago) if last_run_ago else None),
                    "time_until_next": (format_duration(next_run_in) if next_run_in else None),
                }
                timer_tasks.append(task_info)

            running_tasks.append(task_info)

        # Count unique tasks (not subscriptions)
        unique_tasks = len(set(id(sub.subscriber) for sub in self._subscriptions))

        return {
            "running": running_tasks,
            "timers": timer_tasks,
            "count": unique_tasks,
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
                subscriber = timer_sub.subscriber

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

            # Sleep until next timer
            if next_fire_time != float("inf"):
                sleep_time = max(0.001, next_fire_time - current_time)
                await asyncio.sleep(sleep_time)
            else:
                # No active timers, exit the loop
                break


def get_task_manager() -> TaskManager:
    """Get the singleton TaskManager instance."""
    return TaskManager()
