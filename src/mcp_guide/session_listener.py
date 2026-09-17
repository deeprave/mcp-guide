"""Shared lifecycle hooks for state associated with a Guide Session."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from mcp_guide.configuration_update import ConfigurationUpdate
    from mcp_guide.session import Session


class SessionListenerScope(StrEnum):
    """Define whether a listener belongs to one Session or its interaction."""

    SESSION = "session"
    INTERACTION = "interaction"


class SessionListenerTarget(Protocol):
    """Minimum contract for Session-local configuration notifications."""

    async def on_project_changed(self, session: "Session", old_project: str, new_project: str) -> None:
        """Observe a newly bound project for this Session."""

    async def on_configuration_changed(self, session: "Session", update: "ConfigurationUpdate") -> None:
        """Observe a consumer-visible effective configuration change."""


class SessionListener:
    """Base lifecycle for objects observing one Guide Session.

    Session-scoped listeners own project-local state and are recreated for a
    replacement Session. Interaction-scoped listeners own connection protocol
    state and are transferred during a project replacement.
    """

    scope = SessionListenerScope.SESSION

    async def on_project_changed(self, session: "Session", old_project: str, new_project: str) -> None:
        """Observe a newly bound project for this Session."""

    async def on_configuration_changed(self, session: "Session", update: "ConfigurationUpdate") -> None:
        """Observe a consumer-visible effective configuration change."""

    async def on_session_replaced(self, previous: "Session", replacement: "Session") -> None:
        """Transfer interaction-owned state to the active replacement Session."""

    async def on_request_started(self, session: "Session") -> None:
        """Observe the owning connection's next request."""
