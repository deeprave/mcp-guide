"""HTTP transport implementation using MCP's streamable HTTP."""

import asyncio
import errno
import socket
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.auth import AuthEvidence, bind_user_authorisation
from mcp_guide.content_limits import ContentLimits
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.transports import MissingDependencyError
from mcp_guide.transports.rate_limit import HttpRateLimitMiddleware

if TYPE_CHECKING:
    from mcp_guide.auth import AuthService

logger = get_logger(__name__)


class _AuthenticationMiddleware:
    """Pass request evidence to the provider and retain only its opaque result."""

    def __init__(self, application: Callable[..., Any], auth_service: "AuthService") -> None:
        self.application = application
        self.auth_service = auth_service

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.application(scope, receive, send)
            return

        evidence = AuthEvidence(
            headers=tuple(scope.get("headers", ())),
            method=scope.get("method", ""),
            path=scope.get("path", ""),
        )
        try:
            authorisation = await self.auth_service.authenticate(evidence)
        except Exception:
            logger.error("Authentication provider failed while validating a request")
            await send(
                {
                    "type": "http.response.start",
                    "status": 503,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send({"type": "http.response.body", "body": b'{"error":"Authentication unavailable"}'})
            return
        with bind_user_authorisation(authorisation):
            await self.application(scope, receive, send)


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
        content_limits: ContentLimits | None = None,
        auth_service: "AuthService | None" = None,
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
            content_limits: Static server capacity limits for HTTP request admission
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
        self.content_limits = content_limits or ContentLimits.from_config({})
        self.auth_service = auth_service
        self.server: Optional[Any] = None
        self.server_task: Optional[asyncio.Task[None]] = None
        self._listener: socket.socket | None = None

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
        except ImportError as e:
            raise MissingDependencyError(
                "HTTP transport requires uvicorn and starlette. Install with: uv sync --extra http"
            ) from e

        display_host = f"[{self.host}]" if ":" in self.host else self.host
        try:
            if self.auth_service is not None:
                await self.auth_service.start()
            if self.path_prefix:
                endpoint_path = f"/{self.path_prefix.strip('/')}"
                if not endpoint_path.endswith("/mcp"):
                    endpoint_path += "/mcp"
            else:
                endpoint_path = "/mcp"

            # FastMCP 4 owns the Streamable HTTP ASGI application and its
            # lifecycle. Do not reach into the removed FastMCP 3 helper.
            app = self.mcp_server.http_app(
                transport="streamable-http",
                path=endpoint_path,
            )
            session_is_established = _http_session_is_established(app)
            if self.auth_service is not None:
                app = _AuthenticationMiddleware(app, self.auth_service)
            app = HttpRateLimitMiddleware(
                app,
                self.content_limits,
                session_is_established=session_is_established,
            )

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
            if self.host == "::":
                if not socket.has_dualstack_ipv6():
                    raise RuntimeError("Dual-stack IPv4/IPv6 listening is not supported on this platform")
                self._listener = socket.create_server(
                    (self.host, self.port),
                    family=socket.AF_INET6,
                    dualstack_ipv6=True,
                    backlog=config.backlog,
                )

            logger.info(f"HTTP transport started on {self.scheme}://{display_host}:{self.port}{endpoint_path}")

            # Start server in background task
            self.server_task = asyncio.create_task(self._serve(self.server))

        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                raise RuntimeError(
                    f"Port {self.port} is already in use for {self.scheme}://{display_host}:{self.port}. "
                    f"To use a different port, run: mcp-guide {self.scheme}://{display_host}:<port>"
                ) from e
            raise RuntimeError(f"Cannot listen on {self.scheme}://{display_host}:{self.port}: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to start HTTP server on {self.scheme}://{display_host}:{self.port}: {e}") from e
        finally:
            if self.server_task is None:
                self._close_listener()

    async def _serve(self, server: Any) -> None:
        """Retain the explicit listener's ownership through the serving task."""
        try:
            if self._listener is not None:
                await server.serve(sockets=[self._listener])
            else:
                await server.serve()
        finally:
            self._close_listener()

    def _close_listener(self) -> None:
        """Release the transport-owned socket once, including failed startup."""
        if self._listener is not None:
            self._listener.close()
            self._listener = None

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
        finally:
            self._close_listener()
            if self.auth_service is not None:
                await self.auth_service.stop()

    async def send(self, message: Any) -> None:
        """Send a message through HTTP.

        Note: HTTP transport uses request/response pattern, not streaming.
        The MCP protocol over HTTP is handled by FastMCP's http_app()
        which manages the request/response cycle internally.

        Args:
            message: Message to send

        Raises:
            NotImplementedError: HTTP transport does not use send()
        """
        raise NotImplementedError(
            "HTTP transport does not use send() - MCP protocol is handled by FastMCP's http_app()"
        )

    async def receive(self) -> Any:
        """Receive a message from HTTP.

        Note: HTTP transport uses request/response pattern, not streaming.
        The MCP protocol over HTTP is handled by FastMCP's http_app()
        which manages the request/response cycle internally.

        Returns:
            Received message

        Raises:
            NotImplementedError: HTTP transport does not use receive()
        """
        raise NotImplementedError(
            "HTTP transport does not use receive() - MCP protocol is handled by FastMCP's http_app()"
        )


def _http_session_is_established(application: Any) -> Callable[[str], bool]:
    """Return a live Streamable HTTP session lookup for the FastMCP ASGI app."""

    def is_established(session_id: str) -> bool:
        for route in getattr(application, "routes", []):
            endpoint = getattr(route, "endpoint", None)
            while endpoint is not None:
                session_manager = getattr(endpoint, "session_manager", None)
                if session_manager is not None:
                    # FastMCP exposes its stateful Streamable HTTP manager through
                    # the route endpoint. Its live transport map is the only
                    # authoritative record before application request handling.
                    return session_id in session_manager._server_instances
                endpoint = getattr(endpoint, "app", None)
        return False

    return is_established
