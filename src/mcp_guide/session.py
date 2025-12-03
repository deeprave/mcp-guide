"""Session management for per-project runtime state."""

from contextvars import ContextVar
from dataclasses import dataclass, field
from time import time
from typing import Any, Callable, Optional

from mcp_core.mcp_log import get_logger
from mcp_guide.config import ConfigManager
from mcp_guide.models import _NAME_REGEX, Project, SessionState

logger = get_logger(__name__)


@dataclass
class CachedRootsInfo:
    """Cache for MCP client roots and derived project name."""

    roots: list[Any]  # list[Root] when available
    project_name: str
    timestamp: float


@dataclass
class Session:
    """Per-project runtime session (non-singleton)."""

    _config_manager: ConfigManager = field(repr=False)
    project_name: str
    _state: SessionState = field(default_factory=SessionState, init=False)
    _cached_project: Optional[Project] = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Validate project name immediately."""
        if not self.project_name or not self.project_name.strip():
            raise ValueError("Project name cannot be empty")
        if not _NAME_REGEX.match(self.project_name):
            raise ValueError(
                f"Project name '{self.project_name}' must contain only alphanumeric characters, underscores, and hyphens"
            )

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


# ContextVar for async task-local session tracking
active_sessions: ContextVar[dict[str, Session]] = ContextVar("active_sessions")

# ContextVar for async task-local roots cache (thread-safe)
_cached_roots: ContextVar[Optional[CachedRootsInfo]] = ContextVar("cached_roots", default=None)


async def _determine_project_name(ctx: Optional[Any] = None) -> str:
    """Determine project name from MCP client roots or environment.

    Priority:
    1. Client roots (via MCP Context) - PRIMARY
    2. PWD environment variable - FALLBACK (client's PWD if passed via environment)
    3. CWD environment variable - FALLBACK (client's CWD if passed via environment)
    4. Error with instruction

    Note: os.getcwd() is NOT used as it returns the server's CWD, not the client's.
    The server may run in a different process/container from the client.

    Args:
        ctx: Optional MCP Context (FastMCP auto-injects in tools)

    Returns:
        Project name (basename of project directory)

    Raises:
        ValueError: If project name cannot be determined
    """
    import os
    from pathlib import Path
    from urllib.parse import urlparse

    # Priority 1: Client roots (PRIMARY)
    if ctx is not None:
        try:
            roots_result = await ctx.session.list_roots()
            if roots_result.roots:
                first_root = roots_result.roots[0]
                if str(first_root.uri).startswith("file://"):
                    parsed = urlparse(str(first_root.uri))
                    project_path = Path(parsed.path)
                    if project_path.is_absolute():
                        project_name = project_path.name
                        # Cache entire roots list + derived name (thread-safe via ContextVar)
                        _cached_roots.set(
                            CachedRootsInfo(roots=list(roots_result.roots), project_name=project_name, timestamp=time())
                        )
                        return project_name
        except (AttributeError, NotImplementedError):
            # Client doesn't support roots - expected, fall through to next method
            pass
        except Exception as e:
            # Unexpected error - log for debugging but continue to fallback
            logger.debug(f"Failed to get client roots: {e}")

    # Priority 2: PWD environment variable (Unix/Linux shells)
    pwd = os.environ.get("PWD")
    if pwd:
        pwd_path = Path(pwd)
        if pwd_path.is_absolute():
            return pwd_path.name

    # Priority 3: CWD environment variable (alternative to PWD)
    cwd = os.environ.get("CWD")
    if cwd:
        cwd_path = Path(cwd)
        if cwd_path.is_absolute():
            return cwd_path.name

    # Priority 4: Error
    raise ValueError("Project context not available. Call set_project() with the basename of your current directory.")


async def get_or_create_session(
    ctx: Optional[Any] = None,
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
        project_name = await _determine_project_name(ctx)

    # Check if session already exists for this project
    existing_session = get_current_session(project_name)
    if existing_session is not None:
        return existing_session

    # Create new session
    config_manager = ConfigManager(config_dir=_config_dir_for_tests)
    session = Session(_config_manager=config_manager, project_name=project_name)

    # Store in ContextVar
    set_current_session(session)

    return session


def get_current_session(project_name: str) -> Optional[Session]:
    """Get current session for project from ContextVar.

    Args:
        project_name: Name of the project

    Returns:
        Session if exists in current async context, None otherwise

    Note:
        Sessions are isolated per async task using ContextVar.
        Each task has its own session storage.
    """
    sessions = active_sessions.get({})
    return sessions.get(project_name)


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


async def set_project(project_name: str) -> str:
    """Set/load project by name.

    Args:
        project_name: Name of project to set/load

    Returns:
        Success message

    Note:
        Creates or loads project configuration.
        Use when project cannot be auto-detected from context.
    """
    from mcp_core.result import Result

    try:
        session = await get_or_create_session(project_name=project_name)
        # Trigger project load to ensure it exists/is created
        await session.get_project()
        return Result.ok(f"Project '{project_name}' loaded successfully").to_json_str()
    except Exception as e:
        return Result.failure(str(e), error_type="project_load_error").to_json_str()
