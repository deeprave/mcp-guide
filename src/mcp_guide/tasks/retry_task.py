"""RetryTask - monitors and retries unacknowledged instructions."""

from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_init
from mcp_guide.task_manager.interception import EventType
from mcp_guide.task_manager.manager import get_task_manager

if TYPE_CHECKING:
    from mcp_guide.task_manager.manager import EventResult, TaskManager

logger = get_logger(__name__)


@task_init
class RetryTask:
    """Monitor and retry unacknowledged instructions during idle periods."""

    # Number of timer ticks to wait before checking if we should unsubscribe
    STARTUP_GRACE_TICKS = 2

    def __init__(self, task_manager: Optional["TaskManager"] = None) -> None:
        """Initialize RetryTask.

        Args:
            task_manager: TaskManager instance (optional, uses singleton if not provided)
        """
        if task_manager is None:
            task_manager = get_task_manager()
        self.task_manager = task_manager
        self._tick_count = 0

        # Subscribe to timer events with 60-second interval
        self.task_manager.subscribe(self, EventType.TIMER, timer_interval=60.0)

    def get_name(self) -> str:
        """Get task name.

        Returns:
            Task name
        """
        return "RetryTask"

    async def on_init(self) -> None:
        """Initialize task - no-op."""
        pass

    async def on_tool(self) -> None:
        """Called after tool execution - no-op."""
        pass

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> "EventResult | None":
        """Handle timer events and retry unacknowledged instructions.

        Args:
            event_type: Type of event
            data: Event data

        Returns:
            EventResult with result status
        """
        from mcp_guide.task_manager.manager import EventResult

        # Only handle timer events
        if not (event_type & EventType.TIMER):
            return None

        # Increment tick counter
        self._tick_count += 1

        # After grace period, check if we're the only subscriber
        if self._tick_count > self.STARTUP_GRACE_TICKS:
            if self.task_manager.get_subscription_count() == 1:
                logger.info("RetryTask is the only subscriber, unsubscribing")
                await self.task_manager.unsubscribe(self)
                return EventResult(result=True)

        # Only retry when queue is idle
        if not self.task_manager.is_queue_empty():
            return None

        # Retry unacknowledged instructions
        await self.task_manager.retry_unacknowledged()
        return EventResult(result=True)
