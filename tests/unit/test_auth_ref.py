"""Behavioural tests for the reference authentication adapter."""

from __future__ import annotations

import asyncio
import ipaddress
import ssl
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import httpx2
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

if TYPE_CHECKING:
    from mcp_guide.auth_ref import ReferenceAuthProvider


def _provider(handler: httpx2.MockTransport) -> ReferenceAuthProvider:
    """Build the adapter with an in-memory external provider service."""
    from mcp_guide.auth_ref import ReferenceAuthProvider

    client = httpx2.AsyncClient(base_url="https://auth.example", transport=handler)
    return ReferenceAuthProvider(client)


def _self_signed_server_context(tmp_path: Path) -> ssl.SSLContext:
    """Create an untrusted certificate for one local provider-service double."""
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
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    certificate_path = tmp_path / "provider-cert.pem"
    key_path = tmp_path / "provider-key.pem"
    certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    )
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certificate_path, key_path)
    return context


@pytest.mark.anyio
async def test_reference_provider_starts_without_contacting_the_service_then_maps_recognised_scopes() -> None:
    """The external service yields Guide scopes without leaking account identity."""
    from mcp_guide.auth import AuthEvidence, AuthScope

    requests: list[httpx2.Request] = []

    def service(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        if request.headers.get("authorization") is None:
            return httpx2.Response(401)
        return httpx2.Response(200, json={"account_id": "provider-private", "scopes": ["admin"]})

    provider = _provider(httpx2.MockTransport(service))

    await provider.start()
    decision = await provider.authenticate(
        AuthEvidence(headers=((b"authorization", b"Bearer opaque-token"),), method="POST", path="/mcp")
    )
    await provider.stop()

    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert requests[0].url.path == "/v1/authenticate"
    assert requests[0].headers.get("authorization") == "Bearer opaque-token"
    assert decision.scopes == frozenset({AuthScope.USER, AuthScope.ADMIN})


@pytest.mark.anyio
@pytest.mark.parametrize(
    "headers",
    [(), ((b"authorization", b"Basic not-a-bearer"),)],
    ids=["missing", "malformed"],
)
async def test_reference_provider_treats_invalid_bearer_evidence_as_anonymous(
    headers: tuple[tuple[bytes, bytes], ...],
) -> None:
    """Unauthenticated evidence is delegated and never retained as Guide state."""
    from mcp_guide.auth import AuthEvidence

    request_headers: list[str | None] = []

    def service(request: httpx2.Request) -> httpx2.Response:
        request_headers.append(request.headers.get("authorization"))
        return httpx2.Response(401)

    provider = _provider(httpx2.MockTransport(service))
    await provider.start()
    decision = await provider.authenticate(AuthEvidence(headers=headers, method="POST", path="/mcp"))
    await provider.stop()

    assert decision.is_authenticated is False
    assert request_headers == [None]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("response", "error"),
    [
        (httpx2.Response(200, json={"scopes": ["other"]}), "invalid response"),
        (httpx2.Response(200, json={"scopes": ["admin", "admin"]}), "invalid response"),
        (httpx2.Response(200, json={"scopes": "admin"}), "invalid response"),
        (httpx2.Response(200, text="not-json"), "invalid response"),
        (httpx2.Response(503), "unexpected response"),
    ],
)
async def test_reference_provider_rejects_invalid_service_decisions_without_reflecting_bearers(
    response: httpx2.Response,
    error: str,
) -> None:
    """Any malformed or failed decision reaches the transport as a safe failure."""
    from mcp_guide.auth import AuthEvidence
    from mcp_guide.auth_ref import ReferenceAuthProviderError

    def service(request: httpx2.Request) -> httpx2.Response:
        if request.headers.get("authorization") is None:
            return httpx2.Response(401)
        return response

    provider = _provider(httpx2.MockTransport(service))
    await provider.start()
    with pytest.raises(ReferenceAuthProviderError, match=error) as raised:
        await provider.authenticate(
            AuthEvidence(headers=((b"authorization", b"Bearer secret-token"),), method="POST", path="/mcp")
        )
    await provider.stop()

    assert "secret-token" not in str(raised.value)


@pytest.mark.anyio
async def test_reference_provider_refreshes_its_decision_for_every_request() -> None:
    """One connection pool never turns the first caller's scope into session state."""
    from mcp_guide.auth import AuthEvidence, AuthScope

    def service(request: httpx2.Request) -> httpx2.Response:
        token = request.headers.get("authorization")
        if token is None:
            return httpx2.Response(401)
        scopes = [] if token == "Bearer user" else ["admin"]
        return httpx2.Response(200, json={"scopes": scopes})

    provider = _provider(httpx2.MockTransport(service))
    await provider.start()
    user = await provider.authenticate(
        AuthEvidence(headers=((b"authorization", b"Bearer user"),), method="POST", path="/mcp")
    )
    admin = await provider.authenticate(
        AuthEvidence(headers=((b"authorization", b"Bearer admin"),), method="POST", path="/mcp")
    )
    await provider.stop()

    assert user.scopes == frozenset({AuthScope.USER})
    assert admin.scopes == frozenset({AuthScope.USER, AuthScope.ADMIN})


def test_reference_provider_factory_requires_a_provider_owned_https_address(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guide does not invent an endpoint or permit an unencrypted provider connection."""
    from mcp_guide.auth import AuthProviderConfigurationError
    from mcp_guide.auth_ref import create_provider

    monkeypatch.delenv("AG_ADDRESS", raising=False)
    with pytest.raises(AuthProviderConfigurationError, match="AG_ADDRESS"):
        create_provider()

    monkeypatch.setenv("AG_ADDRESS", "http://auth.example")
    with pytest.raises(AuthProviderConfigurationError, match="HTTPS"):
        create_provider()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "failure",
    [
        lambda request: httpx2.ConnectError("connection refused", request=request),
        lambda request: httpx2.ConnectTimeout("connection timed out", request=request),
        lambda request: httpx2.PoolTimeout("connection pool exhausted", request=request),
    ],
    ids=["connection-error", "connection-timeout", "connection-pool-timeout"],
)
async def test_reference_provider_fails_closed_when_the_service_connection_fails(failure) -> None:
    """A network failure cannot be mistaken for an unauthenticated decision."""
    from mcp_guide.auth import AuthEvidence, AuthProviderConnectionError

    def unavailable(request: httpx2.Request) -> httpx2.Response:
        raise failure(request)

    provider = _provider(httpx2.MockTransport(unavailable))

    await provider.start()
    with pytest.raises(AuthProviderConnectionError):
        await provider.authenticate(AuthEvidence(headers=(), method="POST", path="/mcp"))
    await provider.stop()


@pytest.mark.anyio
async def test_reference_provider_reports_a_timed_out_authentication_decision() -> None:
    """A timed-out decision is distinct from a failure to connect to the service."""
    from mcp_guide.auth import AuthEvidence, AuthProviderResponseTimeoutError

    def service(request: httpx2.Request) -> httpx2.Response:
        if request.headers.get("authorization") is None:
            return httpx2.Response(401)
        raise httpx2.ReadTimeout("decision timed out", request=request)

    provider = _provider(httpx2.MockTransport(service))
    await provider.start()
    with pytest.raises(AuthProviderResponseTimeoutError) as raised:
        await provider.authenticate(
            AuthEvidence(headers=((b"authorization", b"Bearer secret-token"),), method="POST", path="/mcp")
        )
    await provider.stop()

    assert "secret-token" not in str(raised.value)


@pytest.mark.anyio
async def test_reference_provider_rejects_an_unexpected_service_response() -> None:
    """A reachable service must still return the documented decision response."""
    from mcp_guide.auth import AuthEvidence
    from mcp_guide.auth_ref import ReferenceAuthProviderError

    provider = _provider(httpx2.MockTransport(lambda request: httpx2.Response(200)))

    await provider.start()
    with pytest.raises(ReferenceAuthProviderError, match="invalid response"):
        await provider.authenticate(AuthEvidence(headers=(), method="POST", path="/mcp"))
    await provider.stop()


@pytest.mark.anyio
async def test_reference_provider_rejects_a_service_certificate_outside_system_trust(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The adapter never weakens TLS verification for a private provider certificate."""
    from mcp_guide.auth import AuthEvidence, AuthProviderConnectionError
    from mcp_guide.auth_ref import create_provider

    async def service(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readuntil(b"\r\n\r\n")
        writer.write(b"HTTP/1.1 401 Unauthorized\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(service, "127.0.0.1", 0, ssl=_self_signed_server_context(tmp_path))
    host, port = server.sockets[0].getsockname()[:2]
    monkeypatch.setenv("AG_ADDRESS", f"https://{host}:{port}")
    provider = create_provider()
    try:
        await provider.start()
        with pytest.raises(AuthProviderConnectionError):
            await provider.authenticate(AuthEvidence(headers=(), method="POST", path="/mcp"))
    finally:
        await provider.stop()
        server.close()
        await server.wait_closed()
