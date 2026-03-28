"""Task protocol and state definitions."""

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from mcp_guide.task_manager.manager import EventResult

from .interception import EventType

# Standard interval for one-shot task initialisation via TIMER_ONCE
DEFAULT_ONCE_INTERVAL = 1.0


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
            EventResult if the event was handled, None if not handled.
            EventResult contains result status and optional message/rendered_content.
        """
        ...

    async def on_tool(self) -> None:
        """Called after every tool/prompt execution.

        Tasks can implement this to perform actions after tool/prompt execution.
        Default implementation does nothing.
        """
        ...


class InitialisableMixin:
    """Mixin for tasks that perform one-shot initialisation via TIMER_ONCE.

    Subclasses implement _initialise() and this mixin wires TIMER_ONCE
    dispatch in handle_event to call it exactly once.
    """

    async def _initialise(self) -> "EventResult":
        """Perform one-shot initialisation. Override in subclass."""
        from mcp_guide.task_manager.manager import EventResult

        return EventResult(result=True)

    async def _handle_timer_once(self, event_type: EventType) -> "EventResult | None":
        """Dispatch TIMER_ONCE to _initialise(). Call from handle_event."""
        if event_type & EventType.TIMER_ONCE:
            return await self._initialise()
        return None
