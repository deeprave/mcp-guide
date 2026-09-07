"""Tests for stdio transport implementation."""

from unittest.mock import AsyncMock, Mock

import pytest

from mcp_guide.transports.stdio import StdioTransport


@pytest.mark.anyio
async def test_stdio_transport_lifecycle():
    """Stdio delegates lifecycle ownership to FastMCP's public runner."""
    # The external SDK runner owns stdin/stdout; keep the substitute at that boundary.
    mock_server = Mock()
    mock_server.run_stdio_async = AsyncMock()

    transport = StdioTransport(mock_server)

    await transport.start()
    mock_server.run_stdio_async.assert_awaited_once_with()

    # The FastMCP runner owns the paired runtime lifespan.
    await transport.stop()
