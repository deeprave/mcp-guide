"""Dynamic standard MCP Skills delivery for Guide packages."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal, cast

from fastmcp.resources.base import InputRequiredResourceResult, Resource
from fastmcp.server.dependencies import get_context
from fastmcp.server.providers.base import Provider
from fastmcp.skills.extension import SkillsExtension
from fastmcp.skills.models import MCPSkill
from mcp.server.context import ServerRequestContext
from mcp.shared.exceptions import MCPError
from mcp_types import INVALID_PARAMS, InputRequiredResult, Notification
from pydantic import AnyUrl, JsonValue

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.result import Result
from mcp_guide.runtime import RequestContext
from mcp_guide.session import request_context_scope
from mcp_guide.tools.tool_resource import (
    GuideSkill,
    _catalogue_description,
    _discover_guide_skills,
    _read_guide_skill,
    parse_standard_skill_uri,
)

logger = get_logger(__name__)
SKILLS_LIST_CHANGED_METHOD = "notifications/skills/list_changed"


class SkillsListChangedNotification(Notification[None, Literal["notifications/skills/list_changed"]]):
    """Ask clients that negotiated Skills to refresh their catalogue."""

    method: Literal["notifications/skills/list_changed"] = SKILLS_LIST_CHANGED_METHOD
    params: None = None


def _skill_uri(name: str) -> str:
    return f"skill://{name}/SKILL.md"


class GuideSkillResource(Resource):
    """Render one standard skill member through Guide's shared resolver."""

    skill_path: str
    guide_session_id: str | None = None
    skill_kwargs: Mapping[str, str | bool] = {}

    async def read(self) -> str | InputRequiredResourceResult:
        context = get_context()
        async with request_context_scope(context, self.guide_session_id, allow_pwd_bootstrap=True) as request_context:
            result = await _read_guide_skill(
                self.skill_path,
                request_context,
                kwargs=self.skill_kwargs,
                mcp_context=context,
                standard_skills=True,
            )
        if isinstance(result, InputRequiredResult):
            return InputRequiredResourceResult(result)
        if not isinstance(result, Result) or not result.success:
            raise MCPError(
                code=INVALID_PARAMS,
                message=getattr(result, "error", None) or f"Guide skill '{self.skill_path}' is unavailable",
            )
        return cast(str, result.value)


class GuideSkillsProvider(Provider):
    """Publish metadata-only Skills entries and render resources only on read."""

    def __init__(self) -> None:
        super().__init__()
        self._catalogue_signature: tuple[tuple[str, str, str, tuple[tuple[str, str], ...]], ...] | None = None

    def required_extensions(self) -> Sequence[SkillsExtension]:
        return (SkillsExtension(providers=[self]),)

    async def _catalogue(self, session_id: str | None = None) -> tuple[RequestContext, dict[str, GuideSkill]]:
        context = get_context()
        async with request_context_scope(context, session_id, allow_pwd_bootstrap=True) as request_context:
            skills = await _discover_guide_skills(request_context.session, request_context.resolve_document_path)
            return request_context, skills

    @staticmethod
    def _signature(skills: Mapping[str, GuideSkill]) -> tuple[tuple[str, str, str, tuple[tuple[str, str], ...]], ...]:
        """Return stable metadata for detecting an effective catalogue change."""
        return tuple(
            (
                name,
                skill.description,
                skill.usage,
                tuple(sorted((key, repr(value)) for key, value in skill.frontmatter.items())),
            )
            for name, skill in sorted(skills.items())
        )

    async def _notify_catalogue_change(self, skills: Mapping[str, GuideSkill]) -> None:
        """Notify the requesting client when rebuilding finds a changed catalogue."""
        signature = self._signature(skills)
        previous = self._catalogue_signature
        self._catalogue_signature = signature
        if previous is None or signature == previous:
            return
        try:
            context = get_context()
            if context.client_supports_extension("io.modelcontextprotocol/skills"):
                await context.send_notification(cast(Any, SkillsListChangedNotification()))
        except RuntimeError:
            return
        except Exception as error:
            logger.debug("Could not send skills catalogue refresh notification: %s", error)

    @staticmethod
    def _entry(skill: GuideSkill, *, bound: bool) -> MCPSkill:
        frontmatter = {
            key: value
            for key, value in skill.frontmatter.items()
            if key not in {"description", "usage", "cache", "instruction", "type"}
        }
        return MCPSkill(
            uri=_skill_uri(skill.name),
            frontmatter=cast(
                Mapping[str, JsonValue],
                {"name": skill.name, "description": _catalogue_description(skill, bound=bound), **frontmatter},
            ),
            resources="dynamic",
        )

    async def _entries(self) -> list[MCPSkill]:
        request_context, skills = await self._catalogue()
        await self._notify_catalogue_change(skills)
        return [self._entry(skill, bound=request_context.is_bound) for skill in skills.values()]

    async def _skill_uris(self, uri: str | None = None) -> Sequence[str]:
        return [entry.uri for entry in await self._entries() if uri is None or entry.uri == uri]

    async def _list_skill_entries(self, context: ServerRequestContext[Any, Any]) -> Sequence[MCPSkill]:
        return await self._entries()

    async def _get_skill_entry(self, uri: str, context: ServerRequestContext[Any, Any]) -> MCPSkill | None:
        return next((entry for entry in await self._entries() if entry.uri == uri), None)

    def _owns_skill_resource(self, uri: str) -> bool:
        return uri.startswith("skill://")

    async def _get_resource(self, uri: str, version: object | None = None) -> Resource | None:
        request = parse_standard_skill_uri(uri)
        if request is None:
            return None
        skill_path, session_id, kwargs = request
        request_context, skills = await self._catalogue(session_id)
        if skill_path.split("/", 1)[0] not in skills:
            return None
        return GuideSkillResource(
            uri=AnyUrl(uri),
            name=skill_path,
            mime_type="text/markdown",
            skill_path=skill_path,
            guide_session_id=session_id,
            skill_kwargs=kwargs,
        )
