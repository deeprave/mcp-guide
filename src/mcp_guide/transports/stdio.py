"""Stdio transport implementation."""

from typing import Any

from mcp.server.fastmcp import FastMCP


class StdioTransport:
    """Transport implementation using stdio streams."""

    def __init__(self, mcp_server: FastMCP) -> None:
        """Initialize STDIO transport.

        Args:
            mcp_server: FastMCP server instance
        """
        self.mcp_server = mcp_server

    async def start(self) -> None:
        """Start the stdio transport."""
        await self.mcp_server.run_stdio_async()

    async def stop(self) -> None:
        """Stop the stdio transport."""
        pass

    async def send(self, message: Any) -> None:
        """Send a message through stdio.

        Args:
            message: Message to send
        """
        raise NotImplementedError("STDIO transport uses run_stdio_async() for message handling")

    async def receive(self) -> Any:
        """Receive a message from stdio.

        Returns:
            Received message
        """
        raise NotImplementedError("STDIO transport uses run_stdio_async() for message handling")
