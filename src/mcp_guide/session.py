"""Session management for per-project runtime state."""

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Protocol, cast

from fastmcp import Context

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.lazy_path import LazyPath
from mcp_guide.mcp_context import cache_mcp_globals
from mcp_guide.models import _NAME_REGEX, Project
from mcp_guide.models.delegate import ProjectDelegate
from mcp_guide.runtime import OwnerKey

if TYPE_CHECKING:
    from mcp_guide.agent_detection import AgentInfo
    from mcp_guide.feature_flags.protocol import FeatureFlags
    from mcp_guide.render.cache import TemplateContextCache
    from mcp_guide.runtime import GuideRuntime
    from mcp_guide.session_listener import SessionListener

from mcp_guide.result import Result

logger = get_logger(__name__)

# Module-level flag to control default profile application
_enable_default_profile = True


class DocrootError(RuntimeError):
    """Raised when `docroot` cannot be created or is invalid."""

    pass


class InvalidGuideSessionError(ValueError):
    """A client supplied a session identifier that FastMCP cannot validate."""

    pass


class UnmintableGuideSessionError(RuntimeError):
    """FastMCP could not mint a session_id for this request's protocol."""

    pass


class ConfigurationService(Protocol):
    """Runtime-owned configuration operations used by Session without importing ConfigManager."""

    def register_session(self, session: object) -> None: ...

    def unregister_session(self, session: object) -> None: ...

    def _invalidate_feature_flags(self) -> None: ...

    async def get_all_project_configs(self) -> dict[str, Project]: ...

    async def resolve_clone_source(self, source_name: str) -> tuple[Project | None, list[str]]: ...

    async def save_project_config(self, project_key: str, project: Project) -> None: ...

    async def get_or_create_project_config(
        self, name: str, *, root_path: Path | None = None
    ) -> tuple[str, Project]: ...

    async def get_project_config_for_root(self, name: str, root_path: Path | None) -> Project | None: ...


class Session:
    """Per-project runtime session with a runtime-owned configuration service."""

    def __init__(
        self,
        runtime: "GuideRuntime[Any]",
    ):
        """Initialise a Session owned by one GuideRuntime.

        Production code MUST obtain Sessions from ``GuideRuntime`` through its
        Session factory. The runtime is private to this Session for its own
        configuration-service access. Other code retrieves the process runtime
        through ``get_runtime()``.

        Tests must use a dedicated GuideRuntime constructed with a config directory.
        """
        self.__delegate: ProjectDelegate = ProjectDelegate()
        self.__bound_root_path: Path | None = None
        self._bind_lock = asyncio.Lock()
        # The validated FastMCP session_id for this Session. It is response
        # data, never an ambient lookup key.
        self.session_id: str | None = None
        self._project_dirty = False
        self._listeners: list["SessionListener"] = []
        self._template_cache: Optional["TemplateContextCache"] = None
        self.command_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
        self._runtime = runtime
        self._config().register_session(self)
        # Session owns its mutable instruction and task lifecycle state.  The
        # transitional accessor remains only for callers not yet migrated.
        from mcp_guide.task_manager.manager import TaskManager

        self.task_manager = TaskManager(self)
        # These subscriptions historically came from import-time singleton
        # construction. They instead belong to this Session's manager so that
        # instruction retries, document ingestion, and update checks cannot
        # cross interaction boundaries.
        try:
            from mcp_guide.tasks.document_task import DocumentTask
            from mcp_guide.tasks.retry_task import RetryTask
            from mcp_guide.tasks.update_task import McpUpdateTask

            RetryTask(self.task_manager)
            DocumentTask(self.task_manager, self)
            McpUpdateTask(self.task_manager, self)
        except Exception as error:
            logger.warning("Unable to initialise Session task subscriptions: %s", error, exc_info=True)

        # MCP context fields (populated by cache_mcp_globals)
        self.agent_info: Optional["AgentInfo"] = None
        self.client_params: Optional[dict[str, Any]] = None

    def _config(self) -> ConfigurationService:
        """Return this Session's runtime-owned configuration service."""
        return cast(ConfigurationService, self._runtime.configuration_service())

    @property
    def project_name(self) -> str:
        """Get the current project name."""
        return self.__delegate.name

    @property
    def project_is_bound(self) -> bool:
        """Whether the session is bound to a real project."""
        return self.__delegate.is_bound

    @property
    def project(self) -> Project | None:
        """Return the Session's current Project, or None when unbound."""
        if not self.__delegate.is_bound:
            return None
        return self.__delegate.project

    @property
    def bound_root_path(self) -> Path | None:
        """The immutable client root selected for this Session, if any."""
        return self.__bound_root_path

    @property
    def active_configuration_identity(self) -> tuple[str, str] | None:
        """Return the exact active configuration identity for runtime publication."""
        if not self.__delegate.is_bound:
            return None
        project = self.__delegate.project
        return (project.name, project.hash) if project.hash is not None else None

    async def bind_project_path(self, path: str | Path) -> None:
        """Bind this unbound Session to an absolute client project root.

        The path is client-supplied identity, not a server filesystem lookup. It is
        validated lexically and retained as the interaction's root identity;
        repeated selection is deliberately rejected.
        """
        from mcp_guide.validation import InvalidProjectNameError

        root_path = Path(path)
        if not LazyPath(path).is_absolute():
            raise InvalidProjectNameError("Project path must be an absolute client filesystem path")
        if ".." in root_path.parts:
            raise InvalidProjectNameError("Project path must not contain directory traversals (..)")
        if not root_path.name or not _NAME_REGEX.match(root_path.name):
            raise InvalidProjectNameError(
                "Project path basename must contain only alphanumeric characters, underscores, and hyphens"
            )

        async with self._bind_lock:
            if self.__bound_root_path is not None:
                raise ValueError("Project root is already bound; begin a new interaction to select another root")

            config_manager = self._config()
            _key, project = await config_manager.get_or_create_project_config(root_path.name, root_path=root_path)
            if self.__bound_root_path is not None:
                raise ValueError("Project root is already bound; begin a new interaction to select another root")
            old_project = self.__delegate.name
            self.__bound_root_path = root_path
            self.__delegate.bind(project)
            self._project_dirty = False
        await self._notify_project_changed(old_project, project.name)

    @property
    def template_cache(self) -> "TemplateContextCache":
        """Get or create the per-session template context cache."""
        if self._template_cache is None:
            from mcp_guide.render.cache import TemplateContextCache

            self._template_cache = TemplateContextCache(self)
            self.add_listener(self._template_cache)
        return self._template_cache

    async def switch_project(self, project_name: str) -> None:
        """Switch this session to a different project.

        Args:
            project_name: Name of the project to switch to

        Raises:
            InvalidProjectNameError: If project name is invalid
        """
        from mcp_guide.validation import InvalidProjectNameError

        if not project_name or not project_name.strip():
            raise InvalidProjectNameError("Project name cannot be empty")

        if project_name.startswith("file://") or os.sep in project_name or (os.altsep and os.altsep in project_name):
            raise InvalidProjectNameError("switch_project accepts a configuration name, not a filesystem path")

        if not _NAME_REGEX.match(project_name):
            raise InvalidProjectNameError(
                f"Project name '{project_name}' must contain only alphanumeric characters, underscores, and hyphens"
            )

        old_project = self.__delegate.name
        if project_name == old_project:
            return

        config_manager = self._config()
        _key, project = await config_manager.get_or_create_project_config(
            project_name, root_path=self.__bound_root_path
        )
        self.__delegate.bind(project)
        self._project_dirty = False
        await self._notify_project_changed(old_project, project_name)

    async def _on_shared_config_changed(self, *, global_changed: bool, project_changed: bool) -> None:
        """Refresh this Session for a scoped shared-configuration publication."""
        if project_changed and self.__delegate.is_bound:
            config_manager = self._config()
            current_project = self.__delegate.project
            try:
                latest_project = await config_manager.get_project_config_for_root(
                    current_project.name, self.__bound_root_path
                )
            except Exception as error:
                logger.debug("Failed to refresh changed project configuration: %s", error, exc_info=True)
                self._project_dirty = True
            else:
                if latest_project is None:
                    # An external writer removed or invalidated the active
                    # entry. Do not silently recreate it while processing a
                    # publication; the next explicit configuration operation
                    # determines whether creation is appropriate.
                    self._project_dirty = True
                else:
                    self.__delegate.bind(latest_project)
                    self._project_dirty = False

        if global_changed:
            self._config()._invalidate_feature_flags()

        await self._notify_config_changed()

    def add_listener(self, listener: "SessionListener") -> None:
        """Add a session change listener."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    async def _notify_project_changed(self, old_project: str, new_project: str) -> None:
        """Notify all listeners of project change."""
        for listener in self._listeners:
            try:
                await listener.on_project_changed(self, old_project, new_project)
            except Exception as e:
                logger.debug(f"Project change listener notification failed: {e}")

    async def _notify_config_changed(self) -> None:
        """Notify all listeners of config change."""
        for listener in self._listeners:
            try:
                await listener.on_config_changed(self)
            except Exception as e:
                logger.debug(f"Config change listener notification failed: {e}")

    async def cleanup(self) -> None:
        """Cleanup resources owned by this Session, including its TaskManager."""
        self._config().unregister_session(self)
        await self.task_manager.cleanup()

    async def get_project(self) -> Project:
        """Get the current project configuration, reloading if stale.

        Raises:
            NoProjectError: If no project is bound to this session.
        """
        if self._project_dirty:
            await self.invalidate_cache()
        return self.__delegate.project

    async def update_config(self, updater: Callable[[Project], Project]) -> None:
        """Update project config using functional pattern."""
        project = await self.get_project()
        updated_project = updater(project)

        if project.key is None:
            raise ValueError("Project key not available")

        config_manager = self._config()
        await config_manager.save_project_config(project.key, updated_project)
        # The writer already has the authoritative immutable value.  Adopt it
        # immediately rather than waiting for the shared-config publication
        # cycle that updates peer Sessions.
        self.__delegate.bind(updated_project)
        self._project_dirty = False

    async def get_all_projects(self) -> dict[str, Project]:
        """Get all project configurations atomically."""
        config_manager = self._config()
        return await config_manager.get_all_project_configs()

    async def resolve_clone_source(self, source_name: str) -> tuple[Project | None, list[str]]:
        """Resolve an explicit clone source through the shared configuration."""
        return await self._config().resolve_clone_source(source_name)

    async def save_project(self, project: Project) -> None:
        """Save project configuration using project's key."""
        if project.key is None:
            raise ValueError("Project key not available")

        config_manager = self._config()
        await config_manager.save_project_config(project.key, project)
        # ``save_project`` can persist a different configuration. Only refresh
        # this interaction when it wrote its own active configuration.
        if self.__delegate.is_bound and self.__delegate.project.key == project.key:
            self.__delegate.bind(project)
            self._project_dirty = False

    async def invalidate_cache(self) -> None:
        """Reload the project configuration from disk."""
        name = self.__delegate.project.name  # raises NoProjectError if unbound
        config_manager = self._config()
        _key, project = await config_manager.get_or_create_project_config(name, root_path=self.__bound_root_path)
        self.__delegate.bind(project)
        self._project_dirty = False

    def project_flags(self, project: Optional[str] = None) -> "FeatureFlags":
        """Get project feature flags proxy."""
        from mcp_guide.feature_flags.project_flags import ProjectFlags

        return ProjectFlags(self)


def _attach_session_listeners(session: Session) -> None:
    """Attach the transitional Session listeners exactly once.

    Keeping listener attachment here gives every runtime-owned Session the
    same Session-local task and rendering lifecycle.
    """
    if getattr(session, "_guide_listeners_attached", False):
        return

    from mcp_guide.guide_uri_listener import GuideUriListener
    from mcp_guide.startup_listener import StartupInstructionListener

    session.add_listener(session.task_manager)
    session.add_listener(StartupInstructionListener())
    session.add_listener(GuideUriListener())
    setattr(session, "_guide_listeners_attached", True)


_USE_PWD_TRUTHY = frozenset({"1", "true", "yes", "on"})


def use_pwd_enabled() -> bool:
    """Whether launch configuration opted into stdio inherited-PWD project binding.

    Off by default. Process ``PWD`` is a client-supplied launch hint, not
    ``getcwd()``: the server filesystem may be a container, an HTTP host, or a
    desktop app started from ``$HOME``. CLI agents that start Guide from the
    project directory may set ``MG_USE_PWD`` to skip one ``set_project``
    round trip.
    """
    return os.environ.get("MG_USE_PWD", "").strip().lower() in _USE_PWD_TRUTHY


async def bind_session_project(session: Session, project_path: str | Path) -> Project:
    """Bind a resolved Session through Guide's single project-binding path.

    Both explicit ``set_project(path)`` and the optional stdio-PWD bootstrap use
    this operation.  Listener attachment happens before binding so the
    Session-owned task and rendering lifecycle observes the initial project
    selection exactly as it does for an explicit bind.
    """
    _attach_session_listeners(session)
    await session.bind_project_path(project_path)
    return await session.get_project()


async def mint_modern_session_id(ctx: "Context") -> str | None:
    """Mint a resumable FastMCP session_id for a modern request.

    This is deliberately the only minting path used by explicit project
    binding and by the optional stdio ``PWD`` bootstrap.  Other sessionless
    modern requests stay request-local and unbound.
    """
    request = getattr(ctx, "request_context", None)
    if request is None or getattr(request, "protocol_version", None) != "2026-07-28":
        return None

    from fastmcp.server.sessions import create_session

    return await create_session()


async def retire_minted_session(ctx: Any | None, session_id: str) -> None:
    """End a FastMCP session and drop its GuideRuntime entry after a failed bind."""
    from fastmcp.server.sessions import end_session

    from mcp_guide.mcp_context import runtime_from_fastmcp

    try:
        await end_session(session_id)
    except Exception:
        logger.warning("Failed to retire a session created for an unsuccessful project binding", exc_info=True)
    runtime = runtime_from_fastmcp(ctx) if ctx is not None else None
    if runtime is not None:
        try:
            await runtime.discard_session(OwnerKey(session_id))
        except Exception:
            logger.warning("Failed to clean up Guide state for an unsuccessful project binding", exc_info=True)


@asynccontextmanager
async def request_context_scope(
    ctx: Any,
    session_id: str | None = None,
    *,
    allow_pwd_bootstrap: bool,
    mint_session_if_unbound: bool = False,
):
    """Resolve one application RequestContext for a public MCP invocation.

    This is the only bridge from FastMCP's request object to Guide application
    state.  Nested application operations receive the yielded context directly;
    they must not resolve an interaction for themselves.
    """
    if ctx is None:
        raise RuntimeError("A public MCP invocation requires a FastMCP context")

    from mcp_guide.mcp_context import runtime_from_fastmcp, session_resolution_from_fastmcp

    runtime = runtime_from_fastmcp(ctx)
    if runtime is None:
        raise RuntimeError("A public MCP invocation requires a GuideRuntime")

    seq = runtime.next_request_seq()
    minted_session_id: str | None = None
    session: Session | None = None

    try:
        protocol_revision, resolved_session_id = session_resolution_from_fastmcp(ctx, session_id=session_id)
    except ValueError as error:
        if session_id is not None:
            raise InvalidGuideSessionError("Invalid or unknown session ID") from error
        raise

    pwd = os.environ.get("PWD")
    pwd_bind = (
        allow_pwd_bootstrap
        and use_pwd_enabled()
        and session_id is None
        and protocol_revision == "2026-07-28"
        and getattr(ctx, "transport", None) == "stdio"
        and bool(pwd)
        and LazyPath(pwd).is_absolute()
    )

    if resolved_session_id is None and mint_session_if_unbound and isinstance(ctx, Context):
        session = await runtime.create_session(ctx)
        minted_session_id = session.session_id
        resolved_session_id = minted_session_id
    elif resolved_session_id is None and pwd_bind and isinstance(ctx, Context):
        session = await runtime.create_session(ctx)
        minted_session_id = session.session_id
        resolved_session_id = minted_session_id

    if resolved_session_id is not None:
        owner = OwnerKey(resolved_session_id)
    else:
        owner = OwnerKey(f"unbound:{seq}")

    async with runtime.session_request(owner):
        if session is None:
            if resolved_session_id is not None:
                if isinstance(ctx, Context):
                    connection_id = getattr(ctx, "session_id", None)
                    handshake_connection = protocol_revision != "2026-07-28" and resolved_session_id == connection_id
                    if not handshake_connection:
                        from fastmcp.server.sessions import InvalidSession
                        from fastmcp.server.sessions import get_session as get_fastmcp_session

                        try:
                            await get_fastmcp_session(resolved_session_id)
                        except InvalidSession as error:
                            raise InvalidGuideSessionError("Invalid or unknown session ID") from error
                await runtime.expire_inactive_sessions()
                session = runtime.get_current_session(resolved_session_id)
            else:
                session = cast(Session, runtime.find_session(owner) or runtime.create_transient_session(owner))
        try:
            if pwd_bind and session_id is None and not session.project_is_bound and pwd is not None:
                await bind_session_project(session, Path(pwd))
            else:
                _attach_session_listeners(session)
            if session.agent_info is None:
                await cache_mcp_globals(ctx, session)
            yield await runtime.request_context(session, session_id=session.session_id, seq=seq)
        finally:
            if session.project_is_bound and not owner.value.startswith("unbound:"):
                runtime.retain_session(owner, session)
            elif minted_session_id is not None:
                await retire_minted_session(ctx, minted_session_id)


async def list_all_projects(session: "Session", verbose: bool = False) -> Result[dict[str, Any]]:
    """List all available projects.

    This is a read-only operation that returns a snapshot of all projects.

    Args:
        verbose: If True, return full project details; if False, return names only
        session: Session for flag resolution

    Returns:
        Result with projects dict
    """
    from mcp_guide.models import format_project_data
    from mcp_guide.result_constants import ERROR_CONFIG_READ, ERROR_INVALID_NAME, ERROR_UNEXPECTED

    try:
        # Verbose: get all project configs in one atomic read
        all_projects = await session.get_all_projects()
        if not verbose:
            # For non-verbose, show project keys when there are name conflicts
            project_list = []
            name_counts: dict[str, int] = {}

            # Count occurrences of each display name
            for key, project in all_projects.items():
                name_counts[project.name] = name_counts.get(project.name, 0) + 1

            # Build the list with disambiguation
            for key in sorted(all_projects.keys()):
                project = all_projects[key]
                if name_counts[project.name] > 1:
                    # Multiple projects with same name - show key for disambiguation
                    project_list.append(f"{project.name} ({key})")
                else:
                    # Unique name - show just the display name
                    project_list.append(project.name)

            return Result.ok({"projects": project_list})

        projects_data = {}
        for name in sorted(all_projects.keys()):
            projects_data[name] = await format_project_data(all_projects[name], verbose=True, session=session)
        return Result.ok({"projects": projects_data})
    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type=ERROR_CONFIG_READ)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_INVALID_NAME)
    except Exception as e:
        logger.exception("Unexpected error listing projects")
        return Result.failure(f"Error listing projects: {e}", error_type=ERROR_UNEXPECTED)
