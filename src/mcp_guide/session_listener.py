"""Session listener protocol for decoupled session change notifications."""

from typing import Protocol


class SessionListener(Protocol):
    """Protocol for objects that listen to session changes."""

    def on_session_changed(self, project_name: str) -> None:
        """Called when session changes to a different project.

        Args:
            project_name: Name of the new project
        """
        ...

    def on_config_changed(self, project_name: str) -> None:
        """Called when project configuration changes.

        Args:
            project_name: Name of the project whose config changed
        """
        ...
