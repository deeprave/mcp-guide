"""Task protocol and state definitions."""

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from mcp_guide.task_manager.manager import EventResult

from .interception import EventType


@runtime_checkable
class TaskSubscriber(Protocol):
    """Protocol for objects that can subscribe to task manager events."""

    def get_name(self) -> str:
        """Get a readable name for the subscriber.

        Returns:
            A string name for the subscriber, defaults to class name with instance ID
        """
        ...

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> "EventResult | None":
        """Handle an event from the task manager.

        Args:
            event_type: The type of event that occurred
            data: Event data dictionary

        Returns:
            EventResult if the event was handled, None if not handled
            EventResult with result status and optional message/rendered_content,
            or bool for backwards compatibility (will be converted to EventResult)
        """
        ...

    async def on_tool(self) -> None:
        """Called after every tool/prompt execution.

        Tasks can implement this to perform actions after tool/prompt execution.
        Default implementation does nothing.
        """
        ...

    async def on_init(self) -> None:
        """Called once during server startup initialization.

        Tasks can implement this to perform one-time initialization before
        any client connections are accepted. This is called after the task
        manager has established a session and loaded resolved flags.

        Default implementation does nothing.
        """
        ...
