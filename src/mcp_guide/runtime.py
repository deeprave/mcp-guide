"""Framework-neutral runtime identities, lifecycle, and request context."""

import asyncio
import os
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.models import NoProjectError, Project
from mcp_guide.utils.project_hash import calculate_project_hash

if TYPE_CHECKING:
    from mcp_guide.configuration import ConfigManager
    from mcp_guide.feature_flags.feature_flags import FeatureFlags
    from mcp_guide.session import Session

SessionT = TypeVar("SessionT")

_GUIDE_RUNTIME: "GuideRuntime[Any] | None" = None


def get_runtime() -> "GuideRuntime[Any]":
    """Return the process GuideRuntime installed by create_runtime()."""
    if _GUIDE_RUNTIME is None:
        raise RuntimeError("Guide runtime has not been created")
    return _GUIDE_RUNTIME


@dataclass(frozen=True)
class OwnerKey:
    """Verified identity used to partition interaction state."""

    value: str


class GuideRuntime(Generic[SessionT]):
    """Process-singleton Guide state with explicit lifecycle and Session ownership."""

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

        # Do not call this constructor. Install the process runtime with create_runtime().
        self._session_factory = session_factory
        self._sessions: dict[OwnerKey, SessionT] = {}
        self._inflight_sessions: dict[OwnerKey, tuple[SessionT, int]] = {}
        self._session_last_used: dict[OwnerKey, float] = {}
        self._session_leases: dict[OwnerKey, int] = {}
        self._request_seq = 0
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
        global _GUIDE_RUNTIME
        async with self._lifecycle_lock:
            if _GUIDE_RUNTIME is not None and _GUIDE_RUNTIME is not self:
                raise RuntimeError("Guide runtime already exists; stop() the current runtime before start()")
            _GUIDE_RUNTIME = self
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
                self._release_process_runtime()
                return
            failure: Exception | None = None
            try:
                sessions = [*self._sessions.values()]
                retained_session_ids = {id(session) for session in sessions}
                sessions.extend(
                    session
                    for session, _count in self._inflight_sessions.values()
                    if id(session) not in retained_session_ids
                )
                for session in sessions:
                    cleanup = getattr(session, "cleanup", None)
                    if cleanup is not None:
                        try:
                            await cleanup()
                        except Exception as error:
                            if failure is None:
                                failure = error
                self._sessions.clear()
                self._inflight_sessions.clear()
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
                self._release_process_runtime()
            if failure is not None:
                raise failure

    def _release_process_runtime(self) -> None:
        """Clear the process runtime when this instance is the installed one."""
        global _GUIDE_RUNTIME
        if _GUIDE_RUNTIME is self:
            _GUIDE_RUNTIME = None

    async def get_docroot(self) -> str:
        """Return the effective docroot owned by the runtime configuration service."""
        get_docroot = getattr(self._config_manager, "get_docroot", None)
        if get_docroot is None:
            raise RuntimeError("GuideRuntime has no docroot-capable configuration service")
        return await get_docroot()

    async def get_docroot_resolver(self) -> Callable[[str | Path], Path]:
        """Await the configured docroot once and return a sync path resolver.

        The configured value is not rewritten. The returned function applies
        LazyPath.resolve() (expandvars, expanduser, resolve) so callers receive
        a host-absolute filesystem path. Containment stays lexical and does not
        follow symlinks.
        """
        from mcp_guide.lazy_path import LazyPath

        raw = await self.get_docroot()
        if not isinstance(raw, str | Path):
            raise TypeError("Document root must be a filesystem path")

        def resolve(relative_path: str | Path) -> Path:
            root = LazyPath(raw).resolve()
            return self._resolve_against_root(root, relative_path)

        return resolve

    def _resolve_against_root(self, root: Path, relative_path: str | Path) -> Path:
        """Resolve a document-root-relative path without following symlinks."""
        requested = Path(relative_path)
        if requested.is_absolute():
            raise ValueError("Document path must be relative to the configured document root")
        candidate = Path(os.path.normpath(str(root / requested)))
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise ValueError("Document path must remain within the configured document root") from error
        return candidate

    async def resolve_document_path(self, relative_path: str | Path) -> Path:
        """Resolve a document-root-relative path to a host-absolute filesystem path.

        Containment is lexical. Absolute paths and ``..`` escapes are rejected.
        Application code should use RequestContext.get_docroot_resolver rather
        than this runtime method or ``get_docroot``.
        """
        return (await self.get_docroot_resolver())(relative_path)

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

    def find_session(self, owner: OwnerKey) -> SessionT | None:
        """Return a retained or in-flight Session without creating state."""
        if session := self._sessions.get(owner):
            return session
        in_flight = self._inflight_sessions.get(owner)
        return in_flight[0] if in_flight is not None else None

    def retain_session(self, owner: OwnerKey, session: SessionT) -> None:
        """Retain a successfully bound Session for later requests."""
        self._sessions[owner] = session
        self._session_last_used[owner] = time.monotonic()

    @asynccontextmanager
    async def session_request(self, owner: OwnerKey) -> AsyncIterator[SessionT]:
        """Yield one request Session and clean it unless it becomes bound/retained."""
        if owner in self._sessions:
            async with self.session_lease(owner):
                yield self._sessions[owner]
            return

        existing = self._inflight_sessions.get(owner)
        if existing is None:
            session = self.create_transient_session(owner)
            count = 0
        else:
            session, count = existing
        self._inflight_sessions[owner] = (session, count + 1)
        try:
            yield session
        finally:
            current = self._inflight_sessions.get(owner)
            if current is not None:
                active_session, active_count = current
                if active_count > 1:
                    self._inflight_sessions[owner] = (active_session, active_count - 1)
                else:
                    self._inflight_sessions.pop(owner, None)
                    if self._sessions.get(owner) is not active_session:
                        cleanup = getattr(active_session, "cleanup", None)
                        if cleanup is not None:
                            await cleanup()

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

    def next_request_seq(self) -> int:
        """Return the next request sequence number for this runtime."""
        self._request_seq += 1
        return self._request_seq

    def get_current_session(self, session_id: str) -> SessionT:
        """Return the Guide Session for a known session_id. Never mint."""
        validate_session_id(session_id)
        owner = OwnerKey(session_id)
        session = self.find_session(owner)
        if session is None:
            session = self.create_transient_session(owner)
            if owner not in self._sessions:
                self._inflight_sessions.setdefault(owner, (session, 0))
        setattr(session, "session_id", session_id)
        return session

    async def create_session(self, ctx: Any) -> SessionT:
        """Mint a FastMCP session_id and attach a Guide Session.

        Call only from PWD bind or set_project when the Session is unbound.
        """
        from mcp_guide.session import UnmintableGuideSessionError, mint_modern_session_id

        minted = await mint_modern_session_id(ctx)
        if minted is None:
            raise UnmintableGuideSessionError("The client protocol cannot carry a Guide session")
        return self.get_current_session(minted)

    async def request_context(
        self,
        session: "Session",
        *,
        session_id: str | None,
        seq: int,
    ) -> "RequestContext":
        """Build the only public RequestContext for a resolved Session."""
        resolver = await get_runtime().get_docroot_resolver()
        return RequestContext(
            session_id=session_id,
            session=session,
            seq=seq,
            document_path_resolver=resolver,
        )


def create_runtime(
    session_factory: Callable[[OwnerKey], SessionT],
    *,
    config_dir: str | None = None,
    docroot: str | Path | None = None,
    on_start: Callable[[], Awaitable[None]] | None = None,
    on_stop: Callable[[], Awaitable[None]] | None = None,
    session_idle_timeout: float | None = 3_600,
) -> GuideRuntime[SessionT]:
    """Construct and install the process GuideRuntime.

    This is the only site that may construct a GuideRuntime.
    Raises if a process runtime is already installed; call stop() first.
    """
    global _GUIDE_RUNTIME
    if _GUIDE_RUNTIME is not None:
        raise RuntimeError("Guide runtime already exists; stop() the current runtime before create_runtime()")
    runtime = GuideRuntime(
        session_factory,
        config_dir=config_dir,
        docroot=docroot,
        on_start=on_start,
        on_stop=on_stop,
        session_idle_timeout=session_idle_timeout,
    )
    _GUIDE_RUNTIME = runtime
    return runtime


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


def validate_session_id(session_id: str | None) -> None:
    """Reject unsafe client session identifiers before they become runtime keys."""
    if session_id is None:
        return
    if (
        not session_id
        or len(session_id) > 512
        or any(ord(character) < 32 or 127 <= ord(character) <= 159 for character in session_id)
    ):
        raise ValueError("session ID must be non-empty, at most 512 characters, and contain no control characters")


@dataclass(frozen=True)
class RequestContext:
    """Resolved Guide state for one application request."""

    session_id: str | None
    session: "Session"
    seq: int
    document_path_resolver: Callable[[str | Path], Path]

    def __post_init__(self) -> None:
        """Reject unsafe session identifiers before they become runtime keys."""
        validate_session_id(self.session_id)

    @property
    def root(self) -> RootIdentity | None:
        """Return the Session's bound root identity, or None when unbound."""
        root_path = self.session.bound_root_path
        if root_path is None:
            return None
        return RootIdentity.from_path(str(root_path))

    @property
    def project(self) -> Project | None:
        """Return the Session's current Project, or None when unbound."""
        return self.session.project

    @property
    def is_bound(self) -> bool:
        """Whether the request has an immutable root and selected Project."""
        return self.root is not None and self.project is not None

    def require_root(self) -> RootIdentity:
        """Return the bound root or reject an unbound request."""
        if self.root is None:
            raise NoProjectError("Request has no bound project root")
        return self.root

    def require_project(self) -> Project:
        """Return the active Project or reject an unbound request."""
        if self.project is None:
            raise NoProjectError("Request has no active project")
        return self.project

    async def process_result(self, result: Any) -> Any:
        """Process an application Result through this request's TaskManager."""
        return await self.session.task_manager.process_result(result)

    def get_docroot_resolver(self) -> Callable[[str | Path], Path]:
        """Return the sync document-path resolver captured for this request.

        The configured document root is not exposed. Each call returns a
        host-absolute path. The function is sync so a hot path can resolve
        many document paths without awaiting each join.
        """
        return self.document_path_resolver

    def resolve_document_path(self, relative_path: str | Path) -> Path:
        """Resolve a document-root-relative path through the request resolver."""
        return self.get_docroot_resolver()(relative_path)
