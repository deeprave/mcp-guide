"""Guide adapter for the external auth-guide reference provider service."""

from __future__ import annotations

import os
import ssl
from collections.abc import Iterable
from typing import Any

import httpx2
import truststore

from mcp_guide.auth import (
    AuthEvidence,
    AuthProviderConfigurationError,
    AuthProviderConnectionError,
    AuthProviderResponseTimeoutError,
    AuthScope,
    UserAuthorisation,
)

AUTHENTICATE_PATH = "/v1/authenticate"
_ADDRESS_ENVIRONMENT_VARIABLE = "AG_ADDRESS"


DEFAULT_TIMEOUT = httpx2.Timeout(5.0)


class ReferenceAuthProviderError(RuntimeError):
    """Raised when the external reference provider cannot make a safe decision."""


class ReferenceAuthProvider:
    """Translate the provider service's narrow decision into Guide scopes."""

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def start(self) -> None:
        """Initialise the local client without probing the external service."""

    async def stop(self) -> None:
        """Close the adapter's connection pool without affecting the service."""
        await self._client.aclose()

    async def authenticate(self, evidence: AuthEvidence) -> UserAuthorisation:
        """Validate opaque bearer evidence through the external provider service."""
        response = await self._request(_bearer_header(evidence.headers))
        if response.status_code == 401:
            return UserAuthorisation(scopes=frozenset())
        if response.status_code != 200:
            raise ReferenceAuthProviderError("Reference authentication service returned an unexpected response")
        return UserAuthorisation(scopes=_scopes_from_response(response))

    async def _request(self, headers: dict[str, str] | None = None) -> httpx2.Response:
        try:
            return await self._client.post(AUTHENTICATE_PATH, headers=headers)
        except httpx2.PoolTimeout as error:
            raise AuthProviderConnectionError() from error
        except httpx2.ConnectTimeout as error:
            raise AuthProviderConnectionError() from error
        except httpx2.TimeoutException as error:
            raise AuthProviderResponseTimeoutError() from error
        except httpx2.RequestError as error:
            raise AuthProviderConnectionError() from error


def create_provider() -> ReferenceAuthProvider:
    """Create the selected adapter from the reference provider's own address setting."""
    address = os.environ.get(_ADDRESS_ENVIRONMENT_VARIABLE)
    if not address:
        raise AuthProviderConfigurationError(f"{_ADDRESS_ENVIRONMENT_VARIABLE} must identify the reference provider")
    if not address.startswith("https://"):
        raise AuthProviderConfigurationError(f"{_ADDRESS_ENVIRONMENT_VARIABLE} must use HTTPS")
    client = httpx2.AsyncClient(
        base_url=address,
        timeout=DEFAULT_TIMEOUT,
        verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
    )
    return ReferenceAuthProvider(client)


def _bearer_header(headers: Iterable[tuple[bytes, bytes]]) -> dict[str, str] | None:
    """Return exactly one opaque bearer header without inspecting its token value."""
    credentials = [value for name, value in headers if name.lower() == b"authorization"]
    if len(credentials) != 1 or not credentials[0].startswith(b"Bearer "):
        return None
    try:
        return {"Authorization": credentials[0].decode("ascii")}
    except UnicodeDecodeError:
        return None


def _scopes_from_response(response: httpx2.Response) -> frozenset[AuthScope]:
    """Accept only the documented scope list and discard all provider metadata."""
    content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
    if content_type != "application/json":
        raise ReferenceAuthProviderError("Reference authentication service returned an invalid response")
    try:
        body: Any = response.json()
    except ValueError as error:
        raise ReferenceAuthProviderError("Reference authentication service returned an invalid response") from error
    if not isinstance(body, dict):
        raise ReferenceAuthProviderError("Reference authentication service returned an invalid response")
    scopes = body.get("scopes")
    if not isinstance(scopes, list) or any(not isinstance(scope, str) for scope in scopes):
        raise ReferenceAuthProviderError("Reference authentication service returned an invalid response")
    if len(set(scopes)) != len(scopes) or any(scope != AuthScope.ADMIN.value for scope in scopes):
        raise ReferenceAuthProviderError("Reference authentication service returned an invalid response")
    result = {AuthScope.USER}
    if AuthScope.ADMIN.value in scopes:
        result.add(AuthScope.ADMIN)
    return frozenset(result)
