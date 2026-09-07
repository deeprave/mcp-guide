"""Tests for HTTP transport implementation."""

import asyncio
import errno
import socket
from unittest.mock import patch

import pytest
from fastmcp import Client

from mcp_guide.transports.http import HttpTransport


class RecordingMcpServer:
    """Record the SDK boundary request and return a minimal ASGI app."""

    def http_app(self, *, transport, path):
        """Mock streamable HTTP app."""
        assert transport == "streamable-http"
        self.endpoint_path = path

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


@pytest.mark.anyio
@pytest.mark.parametrize(
    "prefix,expected", [(None, "/mcp"), ("mcp", "/mcp"), ("api/mcp", "/api/mcp"), ("api", "/api/mcp")]
)
async def test_http_transport_lifecycle(prefix, expected):
    """Test HttpTransport start/stop lifecycle."""
    started = asyncio.Event()
    stopped = asyncio.Event()

    # Control the external Uvicorn boundary; real negotiated clients are tested below.
    class FakeServer:
        def __init__(self, config):
            self.config = config
            self._should_exit = False

        @property
        def should_exit(self):
            return self._should_exit

        @should_exit.setter
        def should_exit(self, value):
            self._should_exit = value
            if value:
                stopped.set()

        async def serve(self):
            started.set()
            await stopped.wait()

    mock_server = RecordingMcpServer()

    with patch("uvicorn.Server", FakeServer):
        transport = HttpTransport("http", "localhost", 8081, mock_server, path_prefix=prefix)

        # Start in background
        await transport.start()

        await started.wait()
        assert mock_server.endpoint_path == expected

        # Verify server started
        assert transport.server is not None
        assert transport.server.config.host == "localhost"
        assert transport.server.config.port == 8081

        # Stop server
        await transport.stop()

        # Verify server stopped
        assert transport.server.should_exit
        assert transport.server_task.done()


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["legacy", "2026-07-28"])
async def test_streamable_http_serves_retained_and_modern_clients(mode: str):
    """FastMCP owns negotiated Streamable HTTP protocol handling."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    with socket.socket() as port_socket:
        try:
            port_socket.bind(("127.0.0.1", 0))
        except OSError as error:
            if error.errno in {errno.EPERM, errno.EACCES}:
                raise pytest.skip(f"HTTP integration test disabled in sandboxed environments: {error}") from error
            raise
        port = port_socket.getsockname()[1]

    application = create_application(ServerConfig())
    transport = HttpTransport("http", "127.0.0.1", port, application.server)
    await transport.start()
    try:
        for _ in range(50):
            if transport.server is not None and transport.server.started:
                break
            await asyncio.sleep(0.01)
        else:
            pytest.fail("Uvicorn did not start")

        async with Client(f"http://127.0.0.1:{port}/mcp", mode=mode) as client:
            tools = await client.list_tools()

        assert any(tool.name == "set_project" for tool in tools)
    finally:
        await transport.stop()
