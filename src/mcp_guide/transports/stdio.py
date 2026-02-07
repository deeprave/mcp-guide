"""Stdio transport implementation."""

from typing import Any


class StdioTransport:
    """Transport implementation using stdio streams."""

    async def start(self) -> None:
        """Start the stdio transport."""
        pass

    async def stop(self) -> None:
        """Stop the stdio transport."""
        pass

    async def send(self, message: Any) -> None:
        """Send a message through stdio.

        Args:
            message: Message to send
        """
        pass

    async def receive(self) -> Any:
        """Receive a message from stdio.

        Returns:
            Received message
        """
        pass
