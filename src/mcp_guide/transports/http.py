"""HTTP transport implementation using MCP's streamable HTTP."""

import asyncio
import errno
from typing import Any, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.transports import MissingDependencyError

logger = get_logger(__name__)


class HttpTransport:
    """Transport implementation using HTTP/HTTPS with MCP's streamable HTTP."""

    def __init__(
        self,
        scheme: str,
        host: Optional[str],
        port: Optional[int],
        mcp_server: Any,
        ssl_certfile: Optional[str] = None,
        ssl_keyfile: Optional[str] = None,
        path_prefix: Optional[str] = None,
        log_level: str = "INFO",
        log_json: bool = False,
    ):
        """Initialize HTTP transport.

        Args:
            scheme: 'http' or 'https'
            host: Host to bind to
            port: Port to bind to
            mcp_server: MCP server instance (FastMCP)
            ssl_certfile: SSL certificate file for HTTPS
            ssl_keyfile: SSL private key file for HTTPS
            path_prefix: Optional path prefix (e.g., 'v1' for /v1/mcp endpoint)
            log_level: Log level for uvicorn
            log_json: Whether to use JSON logging
        """
        self.scheme = scheme
        self.host = host or "localhost"
        self.port = port or (443 if scheme == "https" else 8080)
        self.mcp_server = mcp_server
        self.ssl_certfile = ssl_certfile
        self.ssl_keyfile = ssl_keyfile
        self.path_prefix = path_prefix
        self.log_level = log_level
        self.log_json = log_json
        self.server: Optional[Any] = None
        self.server_task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        """Start the HTTP server using MCP's streamable HTTP (non-blocking)."""
        # Validate SSL configuration
        if self.scheme == "https" and not self.ssl_certfile:
            raise RuntimeError(
                "HTTPS mode requires --ssl-certfile option. "
                "The certificate file must contain the certificate and optionally the private key. "
                "Use --ssl-keyfile if the private key is in a separate file."
            )
        if self.ssl_keyfile and not self.ssl_certfile:
            raise RuntimeError(
                "--ssl-keyfile requires --ssl-certfile. Provide the certificate file with --ssl-certfile."
            )

        try:
            import uvicorn
            from starlette.applications import Starlette
            from starlette.routing import Mount
        except ImportError as e:
            raise MissingDependencyError(
                "HTTP transport requires uvicorn and starlette. Install with: uv sync --extra http"
            ) from e

        try:
            # Get the Starlette app from FastMCP
            mcp_app = self.mcp_server.streamable_http_app()

            # Mount at custom path if provided, otherwise use default
            if self.path_prefix:
                # If path already ends with "mcp", use it as-is; otherwise append "/mcp"
                if self.path_prefix.endswith("mcp"):
                    app = Starlette(routes=[Mount(f"/{self.path_prefix}", app=mcp_app)])
                    endpoint_path = f"/{self.path_prefix}"
                else:
                    app = Starlette(routes=[Mount(f"/{self.path_prefix}", app=mcp_app)])
                    endpoint_path = f"/{self.path_prefix}/mcp"
            else:
                app = mcp_app
                endpoint_path = "/mcp"

            # Configure uvicorn
            from mcp_guide.core.mcp_log import get_uvicorn_log_config

            log_config = get_uvicorn_log_config(self.log_level, self.log_json)

            config = uvicorn.Config(
                app=app,
                host=self.host,
                port=self.port,
                log_config=log_config,
                ssl_certfile=self.ssl_certfile,
                ssl_keyfile=self.ssl_keyfile,
            )

            self.server = uvicorn.Server(config)

            logger.info(f"HTTP transport started on {self.scheme}://{self.host}:{self.port}{endpoint_path}")

            # Start server in background task
            self.server_task = asyncio.create_task(self.server.serve())

        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                raise RuntimeError(
                    f"Port {self.port} is already in use. "
                    f"To use a different port, run: mcp-guide {self.scheme}://{self.host}:<port>"
                ) from e
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to start HTTP server: {e}") from e

    async def stop(self) -> None:
        """Stop the HTTP server."""
        try:
            if self.server:
                self.server.should_exit = True
            if self.server_task:
                await self.server_task
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
