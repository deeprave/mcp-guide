"""Session listener protocol for decoupled session change notifications."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from mcp_guide.session import Session


class SessionListener(Protocol):
    """Protocol for objects that listen to session changes."""

    def on_session_changed(self, session: "Session") -> None:
        """Called when session changes to a different project.

        Args:
            session: Session instance that changed
        """
        ...

    def on_config_changed(self, session: "Session") -> None:
        """Called when project configuration changes.

        Args:
            session: Session instance whose config changed
        """
        ...
