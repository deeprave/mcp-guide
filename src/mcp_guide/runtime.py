"""Framework-neutral runtime identities, lifecycle, and request context."""

import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Generic, Literal, TypeVar

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.models import Project
from mcp_guide.utils.project_hash import calculate_project_hash

if TYPE_CHECKING:
    from mcp_guide.configuration import ConfigManager
    from mcp_guide.feature_flags.feature_flags import FeatureFlags

SessionT = TypeVar("SessionT")


@dataclass(frozen=True)
class OwnerKey:
    """Verified identity used to partition interaction state."""

    value: str


class GuideRuntime(Generic[SessionT]):
    """Process-global Guide state with explicit lifecycle and Session ownership."""

    def __init__(
        self,
        session_factory: Callable[[OwnerKey], SessionT],
        *,
        config_dir: str | None = None,
        docroot: str | Path | None = None,
        on_start: Callable[[], Awaitable[None]] | None = None,
        on_stop: Callable[[], Awaitable[None]] | None = None,
        session_idle_timeout: float | None = 3_600,
    ) -> None:
        from mcp_guide.configuration import ConfigManager

        self._session_factory = session_factory
        self._sessions: dict[OwnerKey, SessionT] = {}
        self._session_last_used: dict[OwnerKey, float] = {}
        self._session_leases: dict[OwnerKey, int] = {}
        if session_idle_timeout is not None and session_idle_timeout <= 0:
            raise ValueError("session_idle_timeout must be positive or None")
        self._session_idle_timeout = session_idle_timeout
        self._config_manager = ConfigManager(config_dir=config_dir, docroot=docroot)
        self._on_start = on_start
        self._on_stop = on_stop
        self._lifecycle_lock = asyncio.Lock()
        self._started = False

    @property
    def started(self) -> bool:
        """Whether process-level runtime initialization has completed."""
        return self._started

    async def start(self) -> None:
        """Run process-level initialization once before request acceptance."""
        async with self._lifecycle_lock:
            if self._started:
                return
            if self._on_start is not None:
                await self._on_start()
            start_config_manager = getattr(self._config_manager, "start", None)
            if start_config_manager is not None:
                await start_config_manager()
            self._started = True

    async def stop(self) -> None:
        """Stop process-level runtime services once after request processing."""
        async with self._lifecycle_lock:
            if not self._started:
                return
            failure: Exception | None = None
            try:
                for session in list(self._sessions.values()):
                    cleanup = getattr(session, "cleanup", None)
                    if cleanup is not None:
                        try:
                            await cleanup()
                        except Exception as error:
                            if failure is None:
                                failure = error
                self._sessions.clear()
                self._session_last_used.clear()
                self._session_leases.clear()
                stop_config_manager = getattr(self._config_manager, "stop", None)
                if stop_config_manager is not None:
                    try:
                        await stop_config_manager()
                    except Exception as error:
                        if failure is None:
                            failure = error
                if self._on_stop is not None:
                    try:
                        await self._on_stop()
                    except Exception as error:
                        if failure is None:
                            failure = error
            finally:
                self._started = False
            if failure is not None:
                raise failure

    async def get_docroot(self) -> str:
        """Return the effective docroot owned by the runtime configuration service."""
        get_docroot = getattr(self._config_manager, "get_docroot", None)
        if get_docroot is None:
            raise RuntimeError("GuideRuntime has no docroot-capable configuration service")
        return await get_docroot()

    def configuration_service(self) -> "ConfigManager":
        """Return the runtime-owned configuration service to a Session."""
        return self._config_manager

    def feature_flags(self) -> "FeatureFlags":
        """Return the global feature-flag handler owned by this runtime."""
        from mcp_guide.feature_flags.feature_flags import FeatureFlags

        return FeatureFlags(self)

    async def get_feature_flags(self) -> dict[str, FeatureValue]:
        """List process-global feature flags persisted by ConfigManager."""
        return await self._config_manager.get_feature_flags()

    async def set_feature_flag(self, flag_name: str, value: FeatureValue) -> None:
        """Set a process-global feature flag."""
        await self._config_manager.set_feature_flag(flag_name, value)

    async def remove_feature_flag(self, flag_name: str) -> None:
        """Remove a process-global feature flag."""
        await self._config_manager.remove_feature_flag(flag_name)

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator["GuideRuntime[SessionT]"]:
        """Expose the runtime lifecycle to FastMCP's public lifespan API."""
        await self.start()
        try:
            yield self
        finally:
            await self.stop()

    def resolve_session(self, owner: OwnerKey) -> SessionT:
        """Return the Session for an owner, creating it once when first needed."""
        if owner not in self._sessions:
            self._sessions[owner] = self._session_factory(owner)
        self._session_last_used[owner] = time.monotonic()
        return self._sessions[owner]

    async def discard_session(self, owner: OwnerKey) -> None:
        """Immediately remove an owner Session whose interaction cannot continue."""
        session = self._sessions.pop(owner, None)
        self._session_last_used.pop(owner, None)
        self._session_leases.pop(owner, None)
        if session is not None:
            cleanup = getattr(session, "cleanup", None)
            if cleanup is not None:
                await cleanup()

    def create_transient_session(self, owner: OwnerKey) -> SessionT:
        """Create request-local unbound state without registering cross-request ownership."""
        return self._session_factory(owner)

    @asynccontextmanager
    async def session_lease(self, owner: OwnerKey) -> AsyncIterator[None]:
        """Keep an already-resolved owner Session alive for one request.

        A lease deliberately does not create state. Callers first resolve and
        validate a request identity, then protect the resulting Session while
        its handler can await arbitrary work.
        """
        if owner not in self._sessions:
            yield
            return
        self._session_leases[owner] = self._session_leases.get(owner, 0) + 1
        try:
            yield
        finally:
            remaining = self._session_leases.get(owner, 1) - 1
            if remaining > 0:
                self._session_leases[owner] = remaining
            else:
                self._session_leases.pop(owner, None)
                if owner in self._sessions:
                    self._session_last_used[owner] = time.monotonic()

    async def expire_inactive_sessions(self, *, now: float | None = None) -> int:
        """Clean up inactive owner Sessions and their contained task state.

        Expiry is evaluated at request boundaries.  This avoids a background
        singleton worker while guaranteeing that a stale owner cannot be
        revived with its previous queues, timers, or rendering cache.
        ``None`` disables idle expiry for deployments that retain their own
        durable interaction state.
        """
        if self._session_idle_timeout is None:
            return 0
        current_time = time.monotonic() if now is None else now
        expired = [
            owner
            for owner, last_used in self._session_last_used.items()
            if current_time - last_used >= self._session_idle_timeout and self._session_leases.get(owner, 0) == 0
        ]
        for owner in expired:
            session = self._sessions.pop(owner, None)
            self._session_last_used.pop(owner, None)
            self._session_leases.pop(owner, None)
            cleanup = getattr(session, "cleanup", None)
            if cleanup is not None:
                await cleanup()
        return len(expired)


@dataclass(frozen=True)
class ClientMetadata:
    """Client display metadata supplied with an MCP request."""

    name: str | None = None
    version: str | None = None


@dataclass(frozen=True)
class RootIdentity:
    """Explicit client filesystem root used for project configuration identity."""

    path: str
    name: str
    hash: str

    @classmethod
    def from_path(cls, path: str) -> "RootIdentity":
        """Build an identity from an absolute client filesystem path."""
        pure_path = PurePath(path)
        if not pure_path.is_absolute():
            raise ValueError("Project path must be absolute")
        return cls(path=str(pure_path), name=pure_path.name, hash=calculate_project_hash(str(pure_path)))


@dataclass(frozen=True)
class RequestContext:
    """Application context derived from one MCP request."""

    protocol_revision: str
    request_id: str | int | None
    owner: OwnerKey
    client: ClientMetadata
    session_id: str | None = None
    session_source: Literal["explicit", "legacy"] | None = None
    root: RootIdentity | None = None
    project: Project | None = None
    session: object | None = None

    def __post_init__(self) -> None:
        """Reject unsafe session identifiers before they become runtime keys."""
        if self.session_id is None:
            return
        if (
            not self.session_id
            or len(self.session_id) > 512
            or any(ord(character) < 32 or 127 <= ord(character) <= 159 for character in self.session_id)
        ):
            raise ValueError("session ID must be non-empty, at most 512 characters, and contain no control characters")
