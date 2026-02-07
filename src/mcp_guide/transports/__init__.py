"""Transport layer for MCP Guide."""

import sys
from typing import Any, Optional

from mcp_guide.transports.base import Transport
from mcp_guide.transports.stdio import StdioTransport


def validate_transport_dependencies(mode: str) -> None:
    """Validate that required dependencies are available for the transport mode.

    Args:
        mode: Transport mode ('stdio', 'http', 'https')

    Raises:
        SystemExit: If required dependencies are missing
    """
    if mode in ("http", "https"):
        try:
            import uvicorn  # noqa: F401
        except ImportError:
            print("Error: HTTP/HTTPS transport requires uvicorn", file=sys.stderr)
            print("Install with: uv sync --extra http", file=sys.stderr)
            print("Or with uvx: uvx --with uvicorn mcp-guide", file=sys.stderr)
            sys.exit(1)


def create_transport(
    mode: str, host: Optional[str], port: Optional[int], mcp_server: Optional[Any] = None
) -> Transport:
    """Create a transport instance based on mode.

    Args:
        mode: Transport mode ('stdio', 'http', 'https')
        host: Host for HTTP/HTTPS transports
        port: Port for HTTP/HTTPS transports
        mcp_server: MCP server instance (required for HTTP/HTTPS)

    Returns:
        Transport instance

    Raises:
        SystemExit: If required dependencies are missing
        ValueError: If mcp_server not provided for HTTP/HTTPS
    """
    validate_transport_dependencies(mode)

    match mode:
        case "stdio":
            return StdioTransport()
        case str(s) if s.startswith("http"):
            if mcp_server is None:
                raise ValueError("mcp_server required for HTTP/HTTPS transport")
            from mcp_guide.transports.http import HttpTransport

            return HttpTransport(mode, host, port, mcp_server)
        case _:
            raise ValueError(f"Unknown transport mode: {mode}")


__all__ = ["Transport", "create_transport", "validate_transport_dependencies"]
