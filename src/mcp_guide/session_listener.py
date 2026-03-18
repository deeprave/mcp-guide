"""Session listener protocol for decoupled session change notifications."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from mcp_guide.session import Session


class SessionListener(Protocol):
    """Protocol for objects that listen to session changes."""

    def on_project_changed(self, session: "Session", old_project: str, new_project: str) -> None:
        """Called when switch_project() changes the active project.

        Args:
            session: Session instance that switched
            old_project: Previous project name (empty string on initial load)
            new_project: New project name
        """
        ...

    def on_config_changed(self, session: "Session") -> None:
        """Called when project configuration changes.

        Args:
            session: Session instance whose config changed
        """
        ...
