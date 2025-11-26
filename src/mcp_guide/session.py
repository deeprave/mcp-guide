"""Session management for per-project runtime state."""

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Callable, Optional

from mcp_guide.config import ConfigManager
from mcp_guide.models import _NAME_REGEX, Project, SessionState


@dataclass
class Session:
    """Per-project runtime session (non-singleton)."""

    config_manager: ConfigManager
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
            self._cached_project = await self.config_manager.get_or_create_project_config(self.project_name)
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
        await self.config_manager.save_project_config(updated_project)
        self._cached_project = updated_project

    def get_state(self) -> SessionState:
        """Get mutable session state."""
        return self._state


# ContextVar for async task-local session tracking
active_sessions: ContextVar[dict[str, Session]] = ContextVar("active_sessions")


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
