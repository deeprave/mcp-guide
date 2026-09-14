"""Session listener protocol for decoupled session change notifications."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from mcp_guide.configuration_update import ConfigurationUpdate
    from mcp_guide.session import Session


class SessionListener(Protocol):
    """Protocol for objects that listen to session changes."""

    async def on_project_changed(self, session: "Session", old_project: str, new_project: str) -> None:
        """Called when switch_project() changes the active project.

        Args:
            session: Session instance that switched
            old_project: Previous project name (empty string on initial load)
            new_project: New project name
        """
        ...

    async def on_configuration_changed(self, session: "Session", update: "ConfigurationUpdate") -> None:
        """Called when a consumer-visible effective configuration changes.

        Args:
            session: Session instance whose config changed
            update: Immutable effective update for the Session's bound project
        """
        ...
