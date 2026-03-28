"""Delegate that wraps an optional Project for deferred binding."""

from typing import Optional

from mcp_guide.models.exceptions import NoProjectError
from mcp_guide.models.project import Project

UNBOUND_PROJECT_NAME = "(unbound)"


class ProjectDelegate:
    """Thin facade over an optional Project.

    Starts unbound (no inner project). Once bound via ``bind()``,
    delegates property access to the real Project. Code that needs
    the actual Project calls ``.project`` which raises
    ``NoProjectError`` when unbound.
    """

    def __init__(self) -> None:
        self._project: Optional[Project] = None

    @property
    def is_bound(self) -> bool:
        """Whether a real project has been bound."""
        return self._project is not None

    @property
    def name(self) -> str:
        """Project name, or placeholder when unbound."""
        return self._project.name if self._project is not None else UNBOUND_PROJECT_NAME

    @property
    def project(self) -> Project:
        """Return the bound Project or raise NoProjectError."""
        if self._project is None:
            raise NoProjectError("Session has no bound project")
        return self._project

    def bind(self, project: Project) -> None:
        """Bind a real project to this delegate."""
        self._project = project
