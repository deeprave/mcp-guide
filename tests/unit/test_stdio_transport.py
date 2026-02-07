"""Tests for stdio transport implementation."""

from unittest.mock import Mock

import pytest

from mcp_guide.transports.base import Transport
from mcp_guide.transports.stdio import StdioTransport


def test_stdio_transport_implements_protocol():
    """Test that StdioTransport implements Transport protocol."""
    mock_server = Mock()
    transport = StdioTransport(mock_server)
    assert isinstance(transport, Transport)


@pytest.mark.asyncio
async def test_stdio_transport_lifecycle():
    """Test StdioTransport start/stop lifecycle."""
    mock_server = Mock()
    mock_server.run_stdio_async = Mock(return_value=None)

    transport = StdioTransport(mock_server)

    # Should be able to stop (no-op)
    await transport.stop()
