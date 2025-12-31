"""Session management for per-project runtime state."""

import asyncio
import contextlib
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Optional

from mcp_core.mcp_log import get_logger

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

if TYPE_CHECKING:
    from mcp_guide.feature_flags.protocol import FeatureFlags
    from mcp_guide.session_listener import SessionListener

from mcp_guide.config import ConfigManager
from mcp_guide.mcp_context import resolve_project_name, resolve_project_path
from mcp_guide.models import _NAME_REGEX, Project, SessionState
from mcp_guide.result import Result
from mcp_guide.watchers.config_watcher import ConfigWatcher

logger = get_logger(__name__)


@dataclass
class Session:
    """Per-project runtime session (non-singleton)."""

    _config_manager: ConfigManager = field(repr=False)
    project_name: str
    _state: SessionState = field(default_factory=SessionState, init=False)
    _cached_project: Optional[Project] = field(default=None, init=False)
    _listeners: list["SessionListener"] = field(default_factory=list, init=False, repr=False)
    _config_watcher: Optional[ConfigWatcher] = field(default=None, init=False, repr=False)
    _watcher_task: Optional["asyncio.Task[None]"] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Validate project name and setup config watcher."""
        from mcp_guide.validation import InvalidProjectNameError

        if not self.project_name or not self.project_name.strip():
            raise InvalidProjectNameError("Project name cannot be empty")
        if not _NAME_REGEX.match(self.project_name):
            raise InvalidProjectNameError(
                f"Project name '{self.project_name}' must contain only alphanumeric characters, underscores, and hyphens"
            )

        # Setup config file watcher
        self._setup_config_watcher()

    def _setup_config_watcher(self) -> None:
        """Setup config file watcher for automatic reload on external changes."""
        try:
            config_file_path = str(self._config_manager.config_file)
            self._config_watcher = ConfigWatcher(
                config_path=config_file_path, callback=self._on_config_file_changed, poll_interval=1.0
            )
            # Watcher will be started lazily when first accessed
            self._watcher_task = None
            self._watcher_lock = asyncio.Lock()
        except asyncio.InvalidStateError as e:
            logger.debug(f"Could not setup config watcher for {self.project_name}: {e}")
        except (PermissionError, OSError, AttributeError) as e:
            logger.warning(f"System error setting up config watcher for {self.project_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error setting up config watcher for {self.project_name}: {e}")
            # Re-raise unexpected errors for proper debugging
            raise

    async def _ensure_watcher_started(self) -> None:
        """Ensure config watcher is started."""
        if self._config_watcher:
            async with self._watcher_lock:
                if self._watcher_task is None or self._watcher_task.done():
                    self._watcher_task = asyncio.create_task(self._config_watcher.start())

    def _on_config_file_changed(self, file_path: str) -> None:
        """Handle config file changes by invalidating cache and notifying sessions."""
        if self._cached_project is None:
            return  # Already invalidated

        logger.warning(f"Configuration file changed externally: {file_path} - reloading session {self.project_name}")

        # Invalidate cached project
        self._cached_project = None

        # Notify all listeners of the change
        self._notify_listeners()

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

    async def cleanup(self) -> None:
        """Cleanup session resources including config watcher."""
        if self._watcher_task and not self._watcher_task.done():
            self._watcher_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._watcher_task
            self._watcher_task = None

        if self._config_watcher:
            try:
                await self._config_watcher.stop()
            except Exception as e:
                logger.debug(f"Error stopping config watcher: {e}")
            self._config_watcher = None

    async def get_project(self) -> Project:
        """Get project configuration (lazy loaded and cached).

        Returns:
            Project configuration

        Note:
            The project config is loaded on first access and cached.
            Subsequent calls return the cached value.
            Use update_config() to modify and persist changes.
        """
        await self._ensure_watcher_started()
        if self._cached_project is None:
            self._cached_project = await self._config_manager.get_or_create_project_config(self.project_name)
        return self._cached_project

    def has_current_session(self) -> bool:
        """Check if session has a current project loaded."""
        return self._cached_project is not None

    def is_watching_config(self) -> bool:
        """Check if session is actively watching config file changes."""
        return self._config_watcher is not None

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

    async def get_docroot(self) -> str:
        """Get document root path for the project.

        Returns:
            Absolute path to the document root directory
        """
        return await self._config_manager.get_docroot()

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


async def resolve_project_by_name(project_name: str, config_manager: ConfigManager) -> str:
    """Resolve project configuration key by display name or project key.

    Args:
        project_name: Display name or project key
        config_manager: Configuration manager for project lookup

    Returns:
        Project display name (for consistency with existing code)

    Note:
        This function handles both display names and project keys.
        If project_name is a project key, uses it directly.
        If project_name is a display name with multiple matches, uses current path hash to select.
        If no matching project exists, the name is returned as-is for creation.
    """
    try:
        # Get all projects to check what we're dealing with
        all_projects = await config_manager.get_all_project_configs()

        # Check if it's an exact key match (hash-suffixed key)
        if project_name in all_projects:
            # If it's a hash-suffixed key, use it directly
            from mcp_guide.utils.project_hash import extract_name_from_key

            if project_name != extract_name_from_key(project_name):
                # This is a hash-suffixed key, use it
                return all_projects[project_name].name

        # Find by display name
        matching_projects = [proj for proj in all_projects.values() if proj.name == project_name]

        if len(matching_projects) == 0:
            # No existing project, return name for creation
            return project_name
        elif len(matching_projects) == 1:
            # Single match, use it
            return project_name
        else:
            # Multiple matches, verify hash
            try:
                current_path = await resolve_project_path()
                from mcp_guide.utils.project_hash import calculate_project_hash

                current_hash = calculate_project_hash(current_path)

                # Find project with matching hash
                for project in matching_projects:
                    if project.hash == current_hash:
                        return project_name

                # No hash match, return name for new project creation
                return project_name

            except ValueError:
                # Cannot determine current path, use first match
                return project_name

    except (ValueError, OSError) as e:
        # Log the error but fallback to original name for robustness
        logger.warning(f"Project resolution failed: {e}")
        return project_name


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

    # Resolve project with hash verification
    config_manager = ConfigManager(config_dir=_config_dir_for_tests)
    resolved_project_name = await resolve_project_by_name(project_name, config_manager)

    # Check if session already exists for this project
    existing_session = get_current_session(resolved_project_name)
    if existing_session is not None:
        return existing_session

    # Create new session
    session = Session(_config_manager=config_manager, project_name=resolved_project_name)

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


async def remove_current_session(project_name: str) -> None:
    """Remove session from ContextVar and cleanup its resources."""
    # Copy to avoid mutating parent context's dict
    sessions = dict(active_sessions.get({}))
    if session := sessions.pop(project_name, None):
        await session.cleanup()

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
    from mcp_guide.result_constants import ERROR_INVALID_NAME
    from mcp_guide.validation import InvalidProjectNameError

    try:
        session = await get_or_create_session(ctx=ctx, project_name=project_name)
        project = await session.get_project()
        return Result.ok(project)
    except (InvalidProjectNameError, ValueError) as e:
        return Result.failure(str(e), error_type=ERROR_INVALID_NAME)
    except Exception as e:
        return Result.failure(str(e), error_type="project_load_error")


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
    from mcp_guide.result_constants import ERROR_INVALID_NAME

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
        return Result.failure(f"Failed to read configuration: {e}", error_type="config_read_error")
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_INVALID_NAME)
    except Exception as e:
        logger.exception("Unexpected error listing projects")
        return Result.failure(f"Error listing projects: {e}", error_type="unexpected_error")


async def resolve_project_name_to_key(name: str, config_manager: "ConfigManager") -> tuple[str, str]:
    """Resolve a project name (display name or key) to the actual project key.

    Args:
        name: Either a display name or a project key
        config_manager: Configuration manager instance

    Returns:
        Tuple of (project_key, display_name)

    Raises:
        ValueError: If project not found or name is ambiguous
    """
    all_projects = await config_manager.get_all_project_configs()

    # First, check if it's an exact key match
    if name in all_projects:
        return name, all_projects[name].name

    # If not a key, try to find by display name
    matching_projects = [(key, proj) for key, proj in all_projects.items() if proj.name == name]

    if not matching_projects:
        raise ValueError(f"Project '{name}' not found")
    elif len(matching_projects) == 1:
        key, project = matching_projects[0]
        return key, project.name
    else:
        # Multiple projects with same display name - user must specify the key
        keys = [key for key, _ in matching_projects]
        raise ValueError(
            f"Multiple projects found with name '{name}'. Please specify the project key: {', '.join(keys)}"
        )


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
    from mcp_guide.result_constants import (
        ERROR_INVALID_NAME,
        ERROR_NO_PROJECT,
        ERROR_NOT_FOUND,
        INSTRUCTION_NO_PROJECT,
        INSTRUCTION_NOTFOUND_ERROR,
    )

    # Get config manager from session if available, otherwise create default
    if session is not None:
        config_manager = session._config_manager
    else:
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
            with contextlib.suppress(Exception):
                session = await get_or_create_session(None)
        # Get all projects in one atomic read
        all_projects = await config_manager.get_all_project_configs()

        # Resolve the project name to a key
        try:
            project_key, display_name = await resolve_project_name_to_key(name, config_manager)
        except ValueError as e:
            return Result.failure(
                str(e),
                error_type=ERROR_NOT_FOUND,
                instruction=INSTRUCTION_NOTFOUND_ERROR,
            )

        # Format and return the requested project
        project_data = await format_project_data(all_projects[project_key], verbose=verbose, session=session)
        # Include project name in response for single project operations
        project_data["project"] = display_name
        return Result.ok(project_data)
    except OSError as e:
        return Result.failure(f"Failed to read project configuration: {e}", error_type="config_read_error")
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_INVALID_NAME)
    except Exception as e:
        logger.exception("Unexpected error getting project info")
        return Result.failure(f"Error retrieving project: {e}", error_type="unexpected_error")
