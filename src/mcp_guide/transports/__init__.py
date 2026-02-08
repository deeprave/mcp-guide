"""Transport layer for MCP Guide."""

from typing import Any, Optional

from mcp_guide.transports.base import Transport
from mcp_guide.transports.stdio import StdioTransport


class MissingDependencyError(RuntimeError):
    """Raised when a required transport dependency is not available."""

    pass


def validate_transport_dependencies(mode: str) -> None:
    """Validate that required dependencies are available for the transport mode.

    Args:
        mode: Transport mode ("stdio", "http", "https")

    Raises:
        MissingDependencyError: If required dependencies are missing.
    """
    if mode in ("http", "https"):
        try:
            import uvicorn  # noqa: F401
        except ImportError as exc:
            raise MissingDependencyError(
                "HTTP/HTTPS transport requires 'uvicorn'. "
                "Install with: 'uv sync --extra http' or "
                "'uvx --with uvicorn mcp-guide'."
            ) from exc


def create_transport(
    mode: str,
    host: Optional[str],
    port: Optional[int],
    mcp_server: Optional[Any] = None,
    ssl_certfile: Optional[str] = None,
    ssl_keyfile: Optional[str] = None,
    path_prefix: Optional[str] = None,
) -> Transport:
    """Create a transport instance based on mode.

    Args:
        mode: Transport mode ('stdio', 'http', 'https')
        host: Host for HTTP/HTTPS transports
        port: Port for HTTP/HTTPS transports
        mcp_server: MCP server instance (required for all transports)
        ssl_certfile: SSL certificate file for HTTPS
        ssl_keyfile: SSL private key file for HTTPS
        path_prefix: Optional path prefix for HTTP endpoint

    Returns:
        Transport instance

    Raises:
        MissingDependencyError: If required dependencies are missing
        ValueError: If mcp_server not provided
    """
    validate_transport_dependencies(mode)

    if mcp_server is None:
        raise ValueError("mcp_server required for transport")

    match mode:
        case "stdio":
            return StdioTransport(mcp_server)
        case str(s) if s.startswith("http"):
            from mcp_guide.transports.http import HttpTransport

            return HttpTransport(mode, host, port, mcp_server, ssl_certfile, ssl_keyfile, path_prefix)
        case _:
            raise ValueError(f"Unknown transport mode: {mode}")


__all__ = ["Transport", "create_transport", "validate_transport_dependencies", "MissingDependencyError"]
