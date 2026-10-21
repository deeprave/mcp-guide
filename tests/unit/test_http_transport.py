"""Tests for HTTP transport implementation."""

import asyncio
import errno
import socket
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
async def test_authentication_middleware_binds_request_evidence_without_calling_provider() -> None:
    """Unprotected requests retain evidence without requiring the provider."""
    observed = []

    async def application(scope, receive, send):
        from mcp_guide.auth import current_auth_evidence

        evidence = current_auth_evidence()
        assert evidence is not None
        assert evidence.method == "POST"
        assert evidence.path == "/mcp"
        assert evidence.headers == ((b"authorization", b"Bearer opaque-token"),)
        observed.append(scope)

    middleware = _AuthenticationMiddleware(application)
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

    assert len(observed) == 1


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
async def test_http_transport_defers_selected_auth_service_until_a_protected_operation() -> None:
    """Transport startup never constructs a configured provider."""
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

    factory_called = False

    class Provider:
        async def start(self) -> None:
            raise AssertionError("Transport startup must not start the provider")

        async def stop(self) -> None:
            raise AssertionError("An unconstructed provider must not be stopped")

        async def authenticate(self, evidence):
            raise AssertionError("No protected operation was invoked")

    def factory() -> Provider:
        nonlocal factory_called
        factory_called = True
        return Provider()

    auth_service = AuthService(factory)
    with patch("uvicorn.Server", FakeServer):
        transport = HttpTransport("http", "localhost", 8081, RecordingMcpServer(), auth_service=auth_service)
        await transport.start()
        await started.wait()
        await transport.stop()

    assert factory_called is False


@pytest.mark.anyio
async def test_reused_http_session_authorises_each_tool_request(tmp_path):
    """An admin-opened session must not retain privileges when credentials change."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    class Provider:
        evidences = []

        async def start(self):
            pass

        async def stop(self):
            pass

        async def authenticate(self, evidence):
            from mcp_guide.auth import AuthProviderConnectionError, AuthProviderResponseTimeoutError

            self.evidences.append(evidence)
            credential = dict(evidence.headers).get(b"authorization")
            if credential == b"Bearer unavailable":
                raise AuthProviderConnectionError()
            if credential == b"Bearer timeout":
                raise AuthProviderResponseTimeoutError()
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
    provider = Provider()
    service = AuthService(lambda: provider)
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
            assert provider.evidences == []
            session_id = bound.structured_content["session_id"]
            http_session_id = client_transport.get_session_id()
            assert http_session_id is not None

            for credential, expected_error, expected_message, value, expected_stored in [
                ("test-admin", None, None, "initial", "initial"),
                (None, "not_authorised", None, "anonymous", "initial"),
                ("test-user", "forbidden", None, "user", "initial"),
                (
                    "unavailable",
                    "authentication_unavailable",
                    "Could not connect to the authentication service",
                    "unavailable",
                    "initial",
                ),
                (
                    "timeout",
                    "authentication_unavailable",
                    "Timed out waiting for an authentication response from the authentication service",
                    "timeout",
                    "initial",
                ),
                ("test-admin", None, None, "restored", "restored"),
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
                    if expected_message is not None:
                        assert result.structured_content["error"] == expected_message
                assert client_transport.get_session_id() == http_session_id
                stored = await application.runtime.feature_flags().get("auth-test")
                assert stored.to_raw() == expected_stored
            assert len(provider.evidences) == 6
    finally:
        await transport.stop()
