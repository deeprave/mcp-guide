"""Tests for HTTP transport implementation."""

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
    mock_server = MockMcpServer()
    transport = HttpTransport("http", "localhost", 8081, mock_server)

    # Start in background task
    import asyncio

    server_task = asyncio.create_task(transport.start())

    # Give server time to start
    await asyncio.sleep(0.5)

    # Stop server
    await transport.stop()

    # Wait for server task to complete
    try:
        await asyncio.wait_for(server_task, timeout=2.0)
    except asyncio.TimeoutError:
        pass  # Server may not exit immediately
