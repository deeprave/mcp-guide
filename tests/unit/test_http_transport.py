"""Tests for HTTP transport implementation."""

from unittest.mock import patch

import pytest

from mcp_guide.transports.base import Transport
from mcp_guide.transports.http import HttpTransport


class MockMcpServer:
    """Mock MCP server for testing."""

    def streamable_http_app(self):
        """Mock streamable HTTP app."""

        # Return a minimal ASGI app
        async def app(scope, receive, send):
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"text/plain"]],
                }
            )
            await send({"type": "http.response.body", "body": b"OK"})

        return app


def test_http_transport_implements_protocol():
    """Test that HttpTransport implements Transport protocol."""
    mock_server = MockMcpServer()
    transport = HttpTransport("http", "localhost", 8080, mock_server)
    assert isinstance(transport, Transport)


def test_https_transport_implements_protocol():
    """Test that HttpTransport works with HTTPS."""
    mock_server = MockMcpServer()
    transport = HttpTransport("https", "0.0.0.0", 443, mock_server)
    assert isinstance(transport, Transport)


@pytest.mark.asyncio
async def test_http_transport_lifecycle():
    """Test HttpTransport start/stop lifecycle."""
    import asyncio

    # Mock uvicorn.Server to avoid real I/O
    class FakeServer:
        def __init__(self, config):
            self.config = config
            self.should_exit = False
            self.started = False

        async def serve(self):
            self.started = True
            while not self.should_exit:
                await asyncio.sleep(0.01)

    mock_server = MockMcpServer()

    with patch("uvicorn.Server", FakeServer):
        transport = HttpTransport("http", "localhost", 8081, mock_server)

        # Start in background
        await transport.start()

        # Give server task time to start
        await asyncio.sleep(0.05)

        # Verify server started
        assert transport.server is not None
        assert transport.server.started

        # Stop server
        await transport.stop()

        # Verify server stopped
        assert transport.server.should_exit
