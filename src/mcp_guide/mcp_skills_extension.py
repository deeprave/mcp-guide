"""Negotiated MCP extension for session-scoped Guide skill discovery."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal, cast
from weakref import WeakKeyDictionary

from fastmcp.server.dependencies import get_context
from fastmcp.server.extensions import MethodBinding, ServerExtension
from mcp.shared.exceptions import MCPError
from mcp_types import INVALID_REQUEST, Notification, Request, RequestParams
from pydantic import BaseModel

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.session import request_context_scope
from mcp_guide.session_listener import SessionListener, SessionListenerScope
from mcp_guide.tools.tool_resource import GuideSkill, discover_guide_skills

if TYPE_CHECKING:
    from mcp.server.context import ServerRequestContext

    from mcp_guide.configuration_update import ConfigurationUpdate
    from mcp_guide.runtime import GuideRuntime
    from mcp_guide.session import Session

logger = get_logger(__name__)

MCP_SKILLS_EXTENSION_ID = "io.uniquode/mcp-guide-skills"
SKILLS_LIST_METHOD = "skills/list"
SKILLS_LIST_CHANGED_METHOD = "notifications/skills/list_changed"


class SkillsListParams(RequestParams):
    """Parameters for the session-scoped ``skills/list`` extension request."""

    session_id: str


class SkillsListRequest(Request[SkillsListParams, Literal["skills/list"]]):
    """Client request for the currently effective Guide skills."""

    method: Literal["skills/list"] = SKILLS_LIST_METHOD
    params: SkillsListParams


class SkillDescription(BaseModel):
    """One serialisable Guide skill in the extension catalogue."""

    identifier: str
    name: str
    description: str
    usage: str
    uri: str

    @classmethod
    def from_skill(cls, skill: GuideSkill) -> "SkillDescription":
        """Convert one internal Guide skill without exposing filesystem state."""
        return cls(
            identifier=skill.identifier,
            name=skill.name,
            description=skill.description,
            usage=skill.usage,
            uri=skill.uri,
        )


class SkillsListResult(BaseModel):
    """Result payload for ``skills/list``."""

    skills: list[SkillDescription]


class SkillsListChangedNotification(Notification[None, Literal["notifications/skills/list_changed"]]):
    """Tell a negotiated client to refresh its effective skill list.

    The notification deliberately has no params payload. The client refreshes
    with ``skills/list`` using its existing opaque Guide session identifier.
    """

    method: Literal["notifications/skills/list_changed"] = SKILLS_LIST_CHANGED_METHOD
    params: None = None


class GuideSkillsExtension(ServerExtension, SessionListener):
    """Expose the active session's effective Guide skills to opted-in clients."""

    identifier = MCP_SKILLS_EXTENSION_ID
    scope = SessionListenerScope.INTERACTION

    def __init__(self, runtime: "GuideRuntime[Session]") -> None:
        """Track lists only for sessions that requested the extension."""
        self._runtime = runtime
        # Last list successfully announced to each session's own connection.
        self._effective_skills: WeakKeyDictionary[Session, tuple[GuideSkill, ...]] = WeakKeyDictionary()
        # A configuration callback can run outside the connection that owns the
        # session. Keep its update until that connection next makes a request.
        self._pending_skills: WeakKeyDictionary[Session, tuple[GuideSkill, ...]] = WeakKeyDictionary()

    def methods(self) -> Sequence[MethodBinding]:
        """Register the additive extension request for modern MCP clients."""
        return (
            MethodBinding(
                method=SKILLS_LIST_METHOD,
                params_type=SkillsListParams,
                handler=self._list_skills,
                protocol_versions=frozenset({"2026-07-28"}),
            ),
        )

    async def _list_skills(
        self,
        server_context: "ServerRequestContext[Any, Any]",
        params: SkillsListParams,
    ) -> SkillsListResult:
        """Return skills for one negotiated, bound Guide session."""
        fastmcp_context = get_context()
        if (
            not fastmcp_context.client_supports_extension(self.identifier)
            or self.client_settings(server_context) is None
        ):
            raise MCPError(
                code=INVALID_REQUEST,
                message=f"{SKILLS_LIST_METHOD} requires the {self.identifier} extension",
            )

        async with request_context_scope(
            fastmcp_context,
            params.session_id,
            allow_pwd_bootstrap=False,
        ) as request_context:
            if not request_context.is_bound:
                raise MCPError(code=INVALID_REQUEST, message="skills/list requires an active bound Guide session")
            skills = tuple(await discover_guide_skills(request_context))
            request_context.session.add_listener(self)
            self._effective_skills[request_context.session] = skills
            self._pending_skills.pop(request_context.session, None)
            return SkillsListResult(skills=[SkillDescription.from_skill(skill) for skill in skills])

    async def on_project_changed(self, session: "Session", old_project: str, new_project: str) -> None:
        """Refresh the tracked list after a binding change."""
        await self._notify_if_effective_skills_changed(session)

    async def on_session_replaced(self, previous: "Session", replacement: "Session") -> None:
        """Keep negotiated client state on the active replacement Session."""
        effective_skills = self._effective_skills.pop(previous, None)
        self._pending_skills.pop(previous, None)
        if effective_skills is None:
            return
        self._effective_skills[replacement] = effective_skills

    async def on_configuration_changed(self, session: "Session", update: "ConfigurationUpdate") -> None:
        """Refresh the tracked list after an effective configuration change."""
        await self._notify_if_effective_skills_changed(session)

    async def on_request_started(self, session: "Session") -> None:
        """Flush a deferred refresh only through the request's owning session."""
        await self._flush_pending_notification(session)

    async def _skills_for_session(self, session: "Session") -> tuple[GuideSkill, ...]:
        """Resolve the effective skills using the same catalogue implementation."""
        if not session.project_is_bound:
            return ()
        request_context = await self._runtime.request_context(
            session,
            session_id=session.session_id,
            seq=self._runtime.next_request_seq(),
        )
        return tuple(await discover_guide_skills(request_context))

    async def _notify_if_effective_skills_changed(self, session: "Session") -> None:
        """Record a changed list and send it only through its owning request."""
        previous = self._effective_skills.get(session)
        if previous is None:
            return
        current = await self._skills_for_session(session)
        if current == previous:
            self._pending_skills.pop(session, None)
            return
        self._pending_skills[session] = current
        await self._flush_pending_notification(session)

    async def _flush_pending_notification(self, session: "Session") -> None:
        """Deliver a pending change only when the current request owns ``session``."""
        current = self._pending_skills.get(session)
        if current is None:
            return
        try:
            fastmcp_context = get_context()
            if fastmcp_context.session_id != session.session_id:
                return
            if not fastmcp_context.client_supports_extension(self.identifier):
                return
            await fastmcp_context.send_notification(cast(Any, SkillsListChangedNotification()))
        except RuntimeError:
            logger.debug("Deferring skills-list refresh until the owning session requests again")
            return
        except Exception as error:
            logger.debug("Deferring failed skills-list refresh: %s", error, exc_info=True)
            return
        self._effective_skills[session] = current
        self._pending_skills.pop(session, None)
