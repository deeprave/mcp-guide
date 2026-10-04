"""Real MCP clients reach one listener through both address families."""

import asyncio
import ipaddress
import socket
import ssl
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx2
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from mcp_guide.auth import AuthEvidence, AuthScope, AuthService, UserAuthorisation
from mcp_guide.cli import ServerConfig
from mcp_guide.server import create_application
from mcp_guide.transports.http import HttpTransport


@pytest.fixture
def ipv6_port() -> int:
    if not socket.has_dualstack_ipv6():
        pytest.skip("Host does not support dual-stack TCP listeners")
    with socket.create_server(("::", 0), family=socket.AF_INET6, dualstack_ipv6=True) as listener:
        return listener.getsockname()[1]


@pytest.fixture
def tls_files(tmp_path: Path) -> tuple[Path, Path, ssl.SSLContext]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.now(timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(hours=1))
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.IPAddress(ipaddress.ip_address("127.0.0.1")), x509.IPAddress(ipaddress.ip_address("::1"))]
            ),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    cert_path, key_path = tmp_path / "cert.pem", tmp_path / "key.pem"
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    )
    return cert_path, key_path, ssl.create_default_context(cafile=str(cert_path))


async def wait_for_listener(transport: HttpTransport) -> None:
    async with asyncio.timeout(10):
        while not transport.server.started:
            if transport.server_task.done():
                await transport.server_task
                pytest.fail("HTTP server stopped before accepting connections")
            await asyncio.sleep(0.01)


class TokenProvider:
    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def authenticate(self, evidence: AuthEvidence) -> UserAuthorisation:
        credential = dict(evidence.headers).get(b"authorization")
        scopes = {
            b"Bearer user": frozenset({AuthScope.USER}),
            b"Bearer admin": frozenset({AuthScope.ADMIN}),
        }.get(credential, frozenset())
        return UserAuthorisation(scopes=scopes)


@pytest.mark.anyio
@pytest.mark.parametrize("scheme", ["http", "https"])
@pytest.mark.parametrize("protected", [False, True])
async def test_dual_stack_mcp_and_authorisation(scheme, protected, ipv6_port, tls_files, tmp_path):
    application = create_application(ServerConfig(transport_mode=scheme, configdir=str(tmp_path)))
    service = AuthService(TokenProvider) if protected else None
    application.runtime.auth_service = service
    cert_path, key_path, tls_context = tls_files
    transport = HttpTransport(
        scheme,
        "::",
        ipv6_port,
        application.server,
        ssl_certfile=str(cert_path) if scheme == "https" else None,
        ssl_keyfile=str(key_path) if scheme == "https" else None,
        auth_service=service,
    )

    def http_client_factory(**kwargs: Any) -> httpx2.AsyncClient:
        return httpx2.AsyncClient(**{**kwargs, "verify": tls_context, "trust_env": False})

    await transport.start()
    try:
        await wait_for_listener(transport)
        for host in ["127.0.0.1", "[::1]"]:
            for credential in [None, "user", "admin"] if protected else [None]:
                client_transport = StreamableHttpTransport(
                    f"{scheme}://{host}:{ipv6_port}/mcp",
                    headers={"authorization": f"Bearer {credential}"} if credential else None,
                    httpx_client_factory=http_client_factory,
                )
                async with Client(client_transport, mode="legacy") as client:
                    assert any(tool.name == "set_project" for tool in await client.list_tools())
                    bound = await client.call_tool("set_project", {"args": {"path": str(tmp_path / "project")}})
                    session_id = bound.structured_content["session_id"]
                    result = await client.call_tool(
                        "set_feature_flag",
                        {"args": {"session_id": session_id, "feature_name": "dual-stack-test", "value": True}},
                        raise_on_error=False,
                    )
                expected_error = {None: "not_authorised", "user": "forbidden", "admin": None}[credential]
                if protected and expected_error:
                    assert result.structured_content["error_type"] == expected_error
                    assert result.is_error is True
                else:
                    assert result.structured_content["success"] is True
    finally:
        await transport.stop()
    with socket.create_server(("::", ipv6_port), family=socket.AF_INET6, dualstack_ipv6=True):
        pass


@pytest.mark.anyio
@pytest.mark.parametrize("host", [None, "localhost", "0.0.0.0", "::1", "dual-stack.test"])
async def test_existing_bind_addresses_are_preserved(host, ipv6_port, tmp_path, monkeypatch):
    original_getaddrinfo = socket.getaddrinfo

    def getaddrinfo(name, *args, **kwargs):
        return original_getaddrinfo("localhost" if name == "dual-stack.test" else name, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
    application = create_application(ServerConfig(configdir=str(tmp_path)))
    transport = HttpTransport("http", host, ipv6_port, application.server)
    await transport.start()
    try:
        await wait_for_listener(transport)
        hosts = ["[::1]"] if host == "::1" else ["127.0.0.1"]
        if host in {None, "localhost", "dual-stack.test"}:
            hosts.append("[::1]")
        for client_host in hosts:
            async with Client(f"http://{client_host}:{ipv6_port}/mcp", mode="legacy") as client:
                assert any(tool.name == "set_project" for tool in await client.list_tools())
        if host in {"0.0.0.0", "::1"}:
            other_host = "[::1]" if host == "0.0.0.0" else "127.0.0.1"
            async with httpx2.AsyncClient(trust_env=False) as client:
                with pytest.raises(httpx2.ConnectError):
                    await client.get(f"http://{other_host}:{ipv6_port}/mcp")
    finally:
        await transport.stop()
