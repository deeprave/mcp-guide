"""Task protocol and state definitions."""

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    pass

from .interception import EventType


@runtime_checkable
class TaskSubscriber(Protocol):
    """Protocol for objects that can subscribe to task manager events."""

    def get_name(self) -> str:
        """Get a readable name for the subscriber.

        Returns:
            A string name for the subscriber, defaults to class name with instance ID
        """
        return f"{self.__class__.__name__}_{id(self)}"

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> bool:
        """Handle an event from the task manager.

        Args:
            event_type: The type of event that occurred
            data: Event data dictionary

        Returns:
            True if the event was handled, False otherwise
        """
        ...
