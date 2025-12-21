"""Session management for per-project runtime state."""

import logging
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Optional

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

if TYPE_CHECKING:
    from mcp_guide.feature_flags.protocol import FeatureFlags
    from mcp_guide.session_listener import SessionListener

from mcp_core.result import Result
from mcp_guide.config import ConfigManager
from mcp_guide.mcp_context import resolve_project_name
from mcp_guide.models import _NAME_REGEX, Project, SessionState

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """Per-project runtime session (non-singleton)."""

    _config_manager: ConfigManager = field(repr=False)
    project_name: str
    _state: SessionState = field(default_factory=SessionState, init=False)
    _cached_project: Optional[Project] = field(default=None, init=False)
    _listeners: list["SessionListener"] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        """Validate project name immediately."""
        from mcp_guide.validation import InvalidProjectNameError

        if not self.project_name or not self.project_name.strip():
            raise InvalidProjectNameError("Project name cannot be empty")
        if not _NAME_REGEX.match(self.project_name):
            raise InvalidProjectNameError(
                f"Project name '{self.project_name}' must contain only alphanumeric characters, underscores, and hyphens"
            )

    def add_listener(self, listener: "SessionListener") -> None:
        """Add a session change listener."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: "SessionListener") -> None:
        """Remove a session change listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        """Notify all listeners of session change."""
        for listener in self._listeners:
            try:
                listener.on_session_changed(self.project_name)
            except Exception as e:
                logger.debug(f"Listener notification failed: {e}")

    async def get_project(self) -> Project:
        """Get project configuration (lazy loaded and cached).

        Returns:
            Project configuration

        Note:
            The project config is loaded on first access and cached.
            Subsequent calls return the cached value.
            Use update_config() to modify and persist changes.
        """
        if self._cached_project is None:
            self._cached_project = await self._config_manager.get_or_create_project_config(self.project_name)
        return self._cached_project

    async def update_config(self, updater: Callable[[Project], Project]) -> None:
        """Update project config using functional pattern.

        Args:
            updater: Function that takes current Project and returns updated Project

        Note:
            The updater function receives the current project config and must
            return a new Project instance (immutable pattern).
            The new config is saved to disk and the cache is updated.
        """
        project = await self.get_project()
        updated_project = updater(project)
        await self._config_manager.save_project_config(updated_project)
        self._cached_project = updated_project

    def get_state(self) -> SessionState:
        """Get mutable session state."""
        return self._state

    def get_docroot(self) -> str:
        """Get document root path for the project.

        Returns:
            Absolute path to the document root directory
        """
        return self._config_manager.get_docroot()

    async def get_all_projects(self) -> dict[str, Project]:
        """Get all project configurations atomically.

        Returns:
            Dictionary mapping project names to Project objects

        Note:
            This is a read-only operation that returns all projects at a point in time.
            Uses file locking to ensure consistency.
        """
        return await self._config_manager.get_all_project_configs()

    async def save_project(self, project: Project) -> None:
        """Save project configuration to disk.

        Args:
            project: Project configuration to save

        Note:
            This operation is atomic and async-safe due to file locking.
            If saving the current project, cache is NOT automatically invalidated.
        """
        await self._config_manager.save_project_config(project)

    def invalidate_cache(self) -> None:
        """Invalidate the cached project configuration.

        Forces the next call to get_project() to reload from disk.
        Use this when the project configuration has been modified externally.
        """
        self._cached_project = None

    def feature_flags(self) -> "FeatureFlags":
        """Get global feature flags proxy.

        Returns:
            GlobalFlags implementation for global flags
        """
        from mcp_guide.feature_flags.global_flags import GlobalFlags

        return GlobalFlags(self._config_manager)

    def project_flags(self, project: Optional[str] = None) -> "FeatureFlags":
        """Get project feature flags proxy.

        Args:
            project: Project name (ignored - always uses current session project)

        Returns:
            ProjectFlags implementation for current project flags
        """
        from mcp_guide.feature_flags.project_flags import ProjectFlags

        return ProjectFlags(self)


# ContextVar for async task-local session tracking
active_sessions: ContextVar[dict[str, Session]] = ContextVar("active_sessions")


async def get_or_create_session(
    ctx: Optional["Context"] = None,  # type: ignore[type-arg]
    project_name: Optional[str] = None,
    _config_dir_for_tests: Optional[str] = None,
) -> Session:
    """Get or create session for project.

    Args:
        ctx: Optional MCP Context (for roots detection)
        project_name: Optional explicit project name (for set_project calls)
        _config_dir_for_tests: Optional config directory for test isolation (internal use only)

    Returns:
        Session for the project

    Raises:
        ValueError: If project name cannot be determined

    Note:
        - If project_name provided: use it directly
        - Else: detect from ctx (checks roots on every call)
        - Creates new session if none exists or project changed
        - Session.get_project() loads full Project from config
    """
    # Determine project name
    if project_name is None:
        # Cache MCP globals if context provided
        if ctx:
            from mcp_guide.mcp_context import cache_mcp_globals

            await cache_mcp_globals(ctx)
        project_name = await resolve_project_name()

    # Check if session already exists for this project
    existing_session = get_current_session(project_name)
    if existing_session is not None:
        return existing_session

    # Create new session
    config_manager = ConfigManager(config_dir=_config_dir_for_tests)
    session = Session(_config_manager=config_manager, project_name=project_name)

    # Register template context cache as listener
    from mcp_guide.utils.template_context_cache import template_context_cache

    session.add_listener(template_context_cache)

    # Store in ContextVar
    set_current_session(session)

    # Notify listeners of session change
    session._notify_listeners()

    return session


def get_current_session(project_name: Optional[str] = None) -> Optional[Session]:
    """Get current session for project from ContextVar.

    Args:
        project_name: Name of the project. If None, returns first available session.

    Returns:
        Session if exists in current async context, None otherwise

    Note:
        Sessions are isolated per async task using ContextVar.
        Each task has its own session storage.
    """
    sessions = active_sessions.get({})
    if project_name is not None:
        return sessions.get(project_name)
    # Return first available session if no project name specified
    return next(iter(sessions.values())) if sessions else None


def set_current_session(session: Session) -> None:
    """Set current session in ContextVar.

    Args:
        session: Session to store in current async context

    Note:
        Creates a copy of the session dict to avoid mutating parent context.
        Sessions are isolated per async task.
    """
    # Copy to avoid mutating parent context's dict
    sessions = dict(active_sessions.get({}))
    sessions[session.project_name] = session
    active_sessions.set(sessions)


def remove_current_session(project_name: str) -> None:
    """Remove session from ContextVar."""
    # Copy to avoid mutating parent context's dict
    sessions = dict(active_sessions.get({}))
    sessions.pop(project_name, None)
    active_sessions.set(sessions)


async def set_project(project_name: str, ctx: Optional["Context"] = None) -> Result[Project]:  # type: ignore[type-arg]
    """Set/load project by name.

    Args:
        project_name: Name of project to set/load
        ctx: Optional MCP Context for roots detection

    Returns:
        Result[Project]: Success with Project object, or failure with error

    Note:
        Creates or loads project configuration.
        Use when project cannot be auto-detected from context.
    """
    from mcp_guide.tools.tool_constants import ERROR_INVALID_NAME
    from mcp_guide.validation import InvalidProjectNameError

    try:
        session = await get_or_create_session(ctx=ctx, project_name=project_name)
        project = await session.get_project()
        return Result.ok(project)
    except InvalidProjectNameError as e:
        return Result.failure(str(e), error_type=ERROR_INVALID_NAME)
    except ValueError as e:
        return Result.failure(str(e), error_type="project_load_error")
    except Exception as e:
        return Result.failure(str(e), error_type="project_load_error")


async def list_all_projects(verbose: bool = False, session: Optional["Session"] = None) -> Result[dict[str, Any]]:
    """List all available projects.

    This is a read-only operation that returns a snapshot of all projects.

    Args:
        verbose: If True, return full project details; if False, return names only
        session: Session for flag resolution (optional)

    Returns:
        Result with projects dict
    """
    from mcp_guide.models import format_project_data
    from mcp_guide.tools.tool_constants import ERROR_INVALID_NAME

    config_manager = ConfigManager()

    try:
        if not verbose:
            # Non-verbose: just return sorted project names
            project_names = await config_manager.list_projects()
            project_names.sort()
            return Result.ok({"projects": project_names})

        # Verbose: get all project configs in one atomic read
        all_projects = await config_manager.get_all_project_configs()
        projects_data = {}
        for name in sorted(all_projects.keys()):
            projects_data[name] = await format_project_data(all_projects[name], verbose=True, session=session)

        return Result.ok({"projects": projects_data})
    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type="config_read_error")
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_INVALID_NAME)
    except Exception as e:
        logger.exception("Unexpected error listing projects")
        return Result.failure(f"Error listing projects: {e}", error_type="unexpected_error")


async def get_project_info(
    name: Optional[str] = None, verbose: bool = False, session: Optional["Session"] = None
) -> Result[dict[str, Any]]:
    """Get information about a specific project by name.

    This is a read-only operation that retrieves project data without side effects.

    Args:
        name: Project name to retrieve. If None, uses current project.
        verbose: If True, include full details; if False, basic info only
        session: Session for flag resolution (optional)

    Returns:
        Result with project data or error:
        - ERROR_NO_PROJECT if no current project and name not provided
        - ERROR_NOT_FOUND if specified project doesn't exist
    """
    from mcp_guide.models import format_project_data
    from mcp_guide.tools.tool_constants import (
        ERROR_INVALID_NAME,
        ERROR_NO_PROJECT,
        ERROR_NOT_FOUND,
        INSTRUCTION_NO_PROJECT,
        INSTRUCTION_NOTFOUND_ERROR,
    )

    config_manager = ConfigManager()

    try:
        # Default to current project if no name provided
        if name is None:
            # Get current project from session
            try:
                if session is None:
                    session = await get_or_create_session(None)
                project = await session.get_project()
                name = project.name
            except ValueError:
                # No current project set
                return Result.failure(
                    "No current project set. Please specify a project name.",
                    error_type=ERROR_NO_PROJECT,
                    instruction=INSTRUCTION_NO_PROJECT,
                )
        elif session is None and verbose:
            # Create session for flag resolution in verbose mode
            try:
                session = await get_or_create_session(None)
            except Exception:
                # If session creation fails, continue without it
                pass

        # Get all projects in one atomic read
        all_projects = await config_manager.get_all_project_configs()

        # Check if requested project exists
        if name not in all_projects:
            return Result.failure(
                f"Project '{name}' not found",
                error_type=ERROR_NOT_FOUND,
                instruction=INSTRUCTION_NOTFOUND_ERROR,
            )

        # Format and return the requested project
        project_data = await format_project_data(all_projects[name], verbose=verbose, session=session)
        # Include project name in response for single project operations
        project_data["project"] = name
        return Result.ok(project_data)
    except OSError as e:
        return Result.failure(f"Failed to read project configuration: {e}", error_type="config_read_error")
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_INVALID_NAME)
    except Exception as e:
        logger.exception("Unexpected error getting project info")
        return Result.failure(f"Error retrieving project: {e}", error_type="unexpected_error")
