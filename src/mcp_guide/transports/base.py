"""Base transport protocol definition."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Transport(Protocol):
    """Protocol for MCP transport implementations."""

    async def start(self) -> None:
        """Start the transport."""
        ...

    async def stop(self) -> None:
        """Stop the transport."""
        ...

    async def send(self, message: Any) -> None:
        """Send a message through the transport.

        Args:
            message: Message to send
        """
        ...

    async def receive(self) -> Any:
        """Receive a message from the transport.

        Returns:
            Received message
        """
        ...
