"""Tests for stdio transport implementation."""

from unittest.mock import AsyncMock, Mock

import pytest

from mcp_guide.transports.base import Transport
from mcp_guide.transports.stdio import StdioTransport


def test_stdio_transport_implements_protocol():
    """Test that StdioTransport implements Transport protocol."""
    mock_server = Mock()
    transport = StdioTransport(mock_server)
    assert isinstance(transport, Transport)


@pytest.mark.anyio
async def test_stdio_transport_lifecycle():
    """Stdio delegates lifecycle ownership to FastMCP's public runner."""
    mock_server = Mock()
    mock_server.run_stdio_async = AsyncMock()

    transport = StdioTransport(mock_server)

    await transport.start()
    mock_server.run_stdio_async.assert_awaited_once_with()

    # The FastMCP runner owns the paired runtime lifespan.
    await transport.stop()
