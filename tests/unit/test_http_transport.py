"""Tests for HTTP transport implementation."""

import asyncio
import errno
import logging
import socket
from types import SimpleNamespace
from unittest.mock import patch

import httpx2
import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from mcp_guide.auth import AuthScope, AuthService, UserAuthorisation
from mcp_guide.transports.http import HttpTransport, _AuthenticationMiddleware


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
async def test_authentication_middleware_passes_request_evidence_to_provider() -> None:
    """The middleware passes request evidence to the provider and calls the application."""
    observed = []

    async def application(scope, receive, send):
        observed.append(scope)

    class AuthService:
        async def authenticate(self, evidence):
            self.evidence = evidence
            return UserAuthorisation(scopes=frozenset({AuthScope.USER}))

    service = AuthService()
    middleware = _AuthenticationMiddleware(application, service)
    await middleware(
        {
            "type": "http",
            "method": "POST",
            "path": "/mcp",
            "headers": [(b"authorization", b"Bearer opaque-token")],
        },
        lambda: None,
        lambda _: None,
    )

    assert service.evidence.method == "POST"
    assert service.evidence.path == "/mcp"
    assert service.evidence.headers == ((b"authorization", b"Bearer opaque-token"),)
    assert len(observed) == 1


@pytest.mark.anyio
async def test_authentication_middleware_does_not_log_provider_exception_text(caplog: pytest.LogCaptureFixture) -> None:
    """Provider failures return a generic response without logging credentials."""
    sent: list[dict] = []

    async def application(scope, receive, send):
        raise AssertionError("The application must not run after provider failure")

    class AuthService:
        async def authenticate(self, evidence):
            raise ValueError("Bearer synthetic-secret")

    async def send(message):
        sent.append(message)

    middleware = _AuthenticationMiddleware(application, AuthService())
    with caplog.at_level(logging.ERROR, logger="mcp_guide.transports.http"):
        await middleware(
            {"type": "http", "method": "POST", "path": "/mcp", "headers": []},
            lambda: None,
            send,
        )

    assert "synthetic-secret" not in caplog.text
    assert "Authentication provider failed while validating a request" in caplog.text
    assert sent == [
        {"type": "http.response.start", "status": 503, "headers": [(b"content-type", b"application/json")]},
        {"type": "http.response.body", "body": b'{"error":"Authentication unavailable"}'},
    ]


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
async def test_http_transport_starts_and_stops_selected_auth_service() -> None:
    """Only the remote transport owns the configured provider lifecycle."""
    started = asyncio.Event()
    stopped = asyncio.Event()

    class FakeServer:
        def __init__(self, config):
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

    class AuthService:
        started = False
        stopped = False

        async def start(self):
            self.started = True

        async def stop(self):
            self.stopped = True

    auth_service = AuthService()
    with patch("uvicorn.Server", FakeServer):
        transport = HttpTransport("http", "localhost", 8081, RecordingMcpServer(), auth_service=auth_service)
        await transport.start()
        await started.wait()
        await transport.stop()

    assert auth_service.started is True
    assert auth_service.stopped is True


@pytest.mark.anyio
async def test_provider_wrapping_preserves_established_session_rate_limiting() -> None:
    """Authentication wrapping retains the FastMCP session lookup for rate limits."""
    session_manager = SimpleNamespace(_server_instances={"established": object()})

    class McpApplication:
        routes = [SimpleNamespace(endpoint=SimpleNamespace(session_manager=session_manager))]

        async def __call__(self, scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})

    class McpServer:
        def http_app(self, *, transport, path):
            return McpApplication()

    class AuthService:
        async def start(self) -> None:
            return None

        async def stop(self) -> None:
            return None

        async def authenticate(self, evidence):
            return UserAuthorisation(scopes=frozenset({AuthScope.USER}))

    captured: list[object] = []

    class FakeServer:
        def __init__(self, config):
            self.should_exit = False
            captured.append(config.app)

        async def serve(self):
            return None

    with patch("uvicorn.Server", FakeServer):
        transport = HttpTransport("http", "localhost", 8081, McpServer(), auth_service=AuthService())
        await transport.start()
        await transport.stop()

    rate_limiter = captured[0]
    assert rate_limiter._session_is_established("established") is True
    assert rate_limiter._session_is_established("missing") is False


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
        for _ in range(200):
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


@pytest.mark.anyio
async def test_reused_http_session_authorises_each_tool_request(tmp_path):
    """An admin-opened session must not retain privileges when credentials change."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    class Provider:
        async def start(self):
            pass

        async def stop(self):
            pass

        async def authenticate(self, evidence):
            credential = dict(evidence.headers).get(b"authorization")
            scopes = {
                b"Bearer test-admin": frozenset({AuthScope.ADMIN}),
                b"Bearer test-user": frozenset({AuthScope.USER}),
            }.get(credential, frozenset())
            return UserAuthorisation(scopes=scopes)

    class ChangingCredentials(httpx2.Auth):
        credential: str | None = "test-admin"

        def auth_flow(self, request):
            if self.credential is not None:
                request.headers["authorization"] = f"Bearer {self.credential}"
            else:
                request.headers.pop("authorization", None)
            yield request

    with socket.socket() as port_socket:
        try:
            port_socket.bind(("127.0.0.1", 0))
        except OSError as error:
            if error.errno in {errno.EPERM, errno.EACCES}:
                raise pytest.skip(f"HTTP integration test disabled in sandboxed environments: {error}") from error
            raise
        port = port_socket.getsockname()[1]

    application = create_application(ServerConfig(transport_mode="http", configdir=str(tmp_path)))
    service = AuthService(Provider)
    application.runtime.auth_service = service
    transport = HttpTransport("http", "127.0.0.1", port, application.server, auth_service=service)
    credentials = ChangingCredentials()
    client_transport = StreamableHttpTransport(f"http://127.0.0.1:{port}/mcp", auth=credentials)
    await transport.start()
    try:
        for _ in range(200):
            if transport.server is not None and transport.server.started:
                break
            await asyncio.sleep(0.01)
        else:
            pytest.fail("Uvicorn did not start")

        async with Client(client_transport, mode="legacy") as client:
            bound = await client.call_tool("set_project", {"args": {"path": str(tmp_path / "client-project")}})
            assert bound.structured_content["success"] is True
            session_id = bound.structured_content["session_id"]
            http_session_id = client_transport.get_session_id()
            assert http_session_id is not None

            for credential, expected_error, value, expected_stored in [
                ("test-admin", None, "initial", "initial"),
                (None, "not_authorised", "anonymous", "initial"),
                ("test-user", "forbidden", "user", "initial"),
                ("test-admin", None, "restored", "restored"),
            ]:
                credentials.credential = credential
                result = await client.call_tool(
                    "set_feature_flag",
                    {"args": {"session_id": session_id, "feature_name": "auth-test", "value": value}},
                    raise_on_error=False,
                )
                assert result.structured_content["success"] is (expected_error is None)
                assert result.is_error is (expected_error is not None)
                if expected_error is not None:
                    assert result.structured_content["error_type"] == expected_error
                assert client_transport.get_session_id() == http_session_id
                stored = await application.runtime.feature_flags().get("auth-test")
                assert stored.to_raw() == expected_stored
    finally:
        await transport.stop()
