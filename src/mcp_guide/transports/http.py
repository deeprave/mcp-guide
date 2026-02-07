"""HTTP transport implementation using MCP's streamable HTTP."""

import errno
from typing import Any, Optional

from mcp_guide.core.mcp_log import get_logger

logger = get_logger(__name__)


class HttpTransport:
    """Transport implementation using HTTP/HTTPS with MCP's streamable HTTP."""

    def __init__(self, scheme: str, host: Optional[str], port: Optional[int], mcp_server: Any):
        """Initialize HTTP transport.

        Args:
            scheme: 'http' or 'https'
            host: Host to bind to
            port: Port to bind to
            mcp_server: MCP server instance (FastMCP)
        """
        self.scheme = scheme
        self.host = host or "localhost"
        self.port = port or (443 if scheme == "https" else 8080)
        self.mcp_server = mcp_server
        self.server: Optional[Any] = None

    async def start(self) -> None:
        """Start the HTTP server using MCP's streamable HTTP."""
        try:
            import uvicorn

            # Get the Starlette app from FastMCP
            app = self.mcp_server.streamable_http_app()

            # Configure uvicorn
            config = uvicorn.Config(
                app=app,
                host=self.host,
                port=self.port,
                log_level="info",
                access_log=True,
            )

            self.server = uvicorn.Server(config)

            logger.info(f"HTTP transport started on {self.scheme}://{self.host}:{self.port}")

            # Start server (this will block until shutdown)
            await self.server.serve()

        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                raise RuntimeError(
                    f"Port {self.port} is already in use. "
                    f"To use a different port, run: mcp-guide {self.scheme}://localhost:<port>"
                ) from e
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to start HTTP server: {e}") from e

    async def stop(self) -> None:
        """Stop the HTTP server."""
        try:
            if self.server:
                self.server.should_exit = True
            logger.info("HTTP transport stopped")
        except Exception as e:
            logger.warning(f"Error during HTTP server shutdown: {e}")

    async def send(self, message: Any) -> None:
        """Send a message through HTTP.

        Note: HTTP transport uses request/response pattern, not streaming.
        The MCP protocol over HTTP is handled by FastMCP's streamable_http_app()
        which manages the request/response cycle internally.

        Args:
            message: Message to send

        Raises:
            NotImplementedError: HTTP transport does not use send()
        """
        raise NotImplementedError(
            "HTTP transport does not use send() - MCP protocol is handled by FastMCP's streamable_http_app()"
        )

    async def receive(self) -> Any:
        """Receive a message from HTTP.

        Note: HTTP transport uses request/response pattern, not streaming.
        The MCP protocol over HTTP is handled by FastMCP's streamable_http_app()
        which manages the request/response cycle internally.

        Returns:
            Received message

        Raises:
            NotImplementedError: HTTP transport does not use receive()
        """
        raise NotImplementedError(
            "HTTP transport does not use receive() - MCP protocol is handled by FastMCP's streamable_http_app()"
        )
