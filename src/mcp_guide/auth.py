"""Provider-neutral authentication contracts for remote MCP transports."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import StrEnum
from importlib.metadata import entry_points
from typing import Any, Protocol, runtime_checkable

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_FORBIDDEN, ERROR_NOT_AUTHORISED

AUTH_PROVIDER_ENTRY_POINT_GROUP = "mcp_guide.auth_providers"
logger = get_logger(__name__)
_USER_AUTHORISATION: ContextVar["UserAuthorisation | None"] = ContextVar("user_authorisation", default=None)


class AuthProviderConfigurationError(ValueError):
    """Raised when a configured provider cannot be resolved safely."""


class AuthProviderResultError(RuntimeError):
    """Raised when a provider returns an invalid authentication decision."""


class AuthScope(StrEnum):
    """Named access scopes returned by a configured authentication provider."""

    USER = "user"
    ADMIN = "admin"


@dataclass(frozen=True)
class AuthEvidence:
    """Ephemeral remote request evidence passed only to an auth provider."""

    headers: tuple[tuple[bytes, bytes], ...]
    method: str
    path: str


@contextmanager
def bind_user_authorisation(authorisation: UserAuthorisation) -> Iterator[None]:
    """Bind a request decision and restore the previous state on every exit."""
    token = _USER_AUTHORISATION.set(authorisation)
    try:
        yield
    finally:
        _USER_AUTHORISATION.reset(token)


def current_user_authorisation() -> UserAuthorisation | None:
    """Return the opaque access state for the current request."""
    return _USER_AUTHORISATION.get()


@dataclass(frozen=True)
class UserAuthorisation:
    """Opaque request-level access result supplied by an authentication provider."""

    scopes: frozenset[AuthScope]
    handoff: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.scopes, frozenset) or not all(isinstance(scope, AuthScope) for scope in self.scopes):
            raise TypeError("UserAuthorisation.scopes must be a frozenset of AuthScope values")

    @property
    def is_authenticated(self) -> bool:
        """User or unrestricted admin access establishes authenticated state."""
        return AuthScope.USER in self.scopes or AuthScope.ADMIN in self.scopes


@runtime_checkable
class AuthProvider(Protocol):
    """An asynchronously managed remote authentication provider."""

    async def start(self) -> None:
        """Initialise provider-owned resources before remote service begins."""

    async def stop(self) -> None:
        """Release provider-owned resources after remote service stops."""

    async def authenticate(self, evidence: AuthEvidence) -> UserAuthorisation:
        """Validate request evidence and return named access scopes."""


@runtime_checkable
class AuthProviderFactory(Protocol):
    """Create one provider instance for a selected remote transport."""

    def __call__(self) -> AuthProvider:
        """Create a provider from its own deployment configuration."""


class AuthService:
    """Own one selected provider for the lifetime of a remote transport."""

    def __init__(self, factory: AuthProviderFactory):
        self._factory = factory
        self._provider: AuthProvider | None = None

    async def start(self) -> None:
        """Construct and start the selected provider once."""
        if self._provider is not None:
            return
        provider = self._factory()
        if not isinstance(provider, AuthProvider):
            raise AuthProviderConfigurationError("Authentication provider does not implement the required protocol")
        self._provider = provider
        try:
            await provider.start()
        except BaseException:
            try:
                await self.stop()
            except BaseException:
                logger.error("Authentication provider cleanup failed after startup failure")
            raise

    async def stop(self) -> None:
        """Stop the selected provider after the remote transport exits."""
        provider, self._provider = self._provider, None
        if provider is not None:
            await provider.stop()

    async def authenticate(self, evidence: AuthEvidence) -> UserAuthorisation:
        """Resolve the selected provider's request-level access scopes."""
        if self._provider is None:
            raise RuntimeError("Authentication provider is not started")
        authorisation = await self._provider.authenticate(evidence)
        if not isinstance(authorisation, UserAuthorisation):
            raise AuthProviderResultError("Authentication provider returned an invalid authorisation result")
        return authorisation


def load_auth_provider_factory(provider_name: str) -> AuthProviderFactory:
    """Load exactly one configured provider factory from package entry points."""

    candidates = entry_points(group=AUTH_PROVIDER_ENTRY_POINT_GROUP)
    selected = [candidate for candidate in candidates if candidate.name == provider_name]
    if not selected:
        raise AuthProviderConfigurationError(
            f"Authentication provider {provider_name!r} is not installed in {AUTH_PROVIDER_ENTRY_POINT_GROUP}"
        )
    if len(selected) > 1:
        raise AuthProviderConfigurationError(f"Authentication provider {provider_name!r} is registered more than once")

    try:
        factory: Any = selected[0].load()
    except Exception as error:
        raise AuthProviderConfigurationError(
            f"Unable to load authentication provider {provider_name!r}: {error}"
        ) from error
    if not callable(factory):
        raise AuthProviderConfigurationError(
            f"Authentication provider {provider_name!r} does not expose a callable factory"
        )
    return factory


def auth_service_for(provider_name: str) -> AuthService:
    """Create a lazy service whose provider is loaded only at transport start."""

    def factory() -> AuthProvider:
        return load_auth_provider_factory(provider_name)()

    return AuthService(factory)


def scope_authorisation_result(
    authorisation: UserAuthorisation | None,
    required_scope: AuthScope,
) -> Result[Any] | None:
    """Map request scopes to the protected-operation result contract."""
    if authorisation is None or not authorisation.is_authenticated:
        error_data = {"handoff": authorisation.handoff} if authorisation and authorisation.handoff else None
        return Result.failure("Authentication is required", error_type=ERROR_NOT_AUTHORISED, error_data=error_data)
    if required_scope not in authorisation.scopes and AuthScope.ADMIN not in authorisation.scopes:
        return Result.failure("Authentication does not permit this operation", error_type=ERROR_FORBIDDEN)
    return None


async def template_auth_context(
    authorisation: UserAuthorisation | None,
) -> dict[str, Any]:
    """Project access predicates from a provider decision bound to this request.

    Template activity means a request decision is present, not that transport
    enforcement is configured. An anonymous decision is still active; absent
    decision state retains the unrestricted rendering defaults.
    """
    request_has_provider_decision = authorisation is not None
    if authorisation is None:
        return {
            "active": request_has_provider_decision,
            "authenticated": True,
            "user": True,
            "admin": True,
        }
    admin = AuthScope.ADMIN in authorisation.scopes
    user = authorisation.is_authenticated
    return {
        "active": request_has_provider_decision,
        "authenticated": user,
        "user": user,
        "admin": admin,
    }
