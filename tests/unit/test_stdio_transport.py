"""Tests for stdio transport implementation."""

import pytest

from mcp_guide.transports.base import Transport
from mcp_guide.transports.stdio import StdioTransport


def test_stdio_transport_implements_protocol():
    """Test that StdioTransport implements Transport protocol."""
    transport = StdioTransport()
    assert isinstance(transport, Transport)


@pytest.mark.asyncio
async def test_stdio_transport_lifecycle():
    """Test StdioTransport start/stop lifecycle."""
    transport = StdioTransport()

    # Should be able to start
    await transport.start()

    # Should be able to stop
    await transport.stop()
