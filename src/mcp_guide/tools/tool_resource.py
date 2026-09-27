# See src/mcp_guide/tools/README.md for tool documentation standards

"""Read resource tool for resolving guide:// URIs."""

import time
from collections.abc import Mapping
from dataclasses import dataclass
from glob import has_magic
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any
from urllib.parse import parse_qs, urlsplit

from anyio import Path as AsyncPath
from fastmcp import Context
from mcp_types import InputRequiredResult
from pydantic import Field, ValidationError, model_validator

from mcp_guide.config_constants import COMMANDS_DIR, SKILLS_DIR
from mcp_guide.content.utils import gather_policy_partials
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.core.validation import validate_content_name
from mcp_guide.discovery.commands import discover_commands, normalise_alias_metadata
from mcp_guide.discovery.files import discover_document_files
from mcp_guide.feature_flags.constants import FLAG_GUIDE_DEVELOPMENT
from mcp_guide.feature_flags.validators import is_value_true
from mcp_guide.models import resolve_all_flags
from mcp_guide.prompts.command_parser import parse_command_arguments
from mcp_guide.render.context import TemplateContext, keyword_context
from mcp_guide.render.frontmatter import check_frontmatter_requirements, parse_content_with_frontmatter
from mcp_guide.render.rendering import render_content
from mcp_guide.result import Result
from mcp_guide.result_constants import (
    AGENT_INFO,
    ERROR_NOT_FOUND,
    ERROR_VALIDATION,
    INSTRUCTION_AGENT_INFORMATION,
    INSTRUCTION_DISPLAY_ONLY,
    USER_INFO,
)
from mcp_guide.runtime import RequestContext, get_runtime
from mcp_guide.skill_elicitation import resolve_skill_elicitations
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content
from mcp_guide.tools.tool_result import ToolResult, tool_result
from mcp_guide.uri_parser import parse_guide_uri

logger = get_logger(__name__)


@dataclass(frozen=True)
class GuideSkill:
    """A Guide skill package rooted at a rendered SKILL.md entrypoint."""

    name: str
    description: str
    usage: str
    frontmatter: Mapping[str, object]
    requirements: Mapping[str, object]
    package_root: PurePosixPath

    @property
    def uri(self) -> str:
        """Return the package's stable Guide resource URI."""
        return f"guide://${self.name}"

    @property
    def entrypoint_path(self) -> str:
        """Return the package-relative public entrypoint path."""
        return f"{self.name}/SKILL.md"


def _visible_guide_skills(discovered: Mapping[str, GuideSkill], flags: Mapping[str, object]) -> dict[str, GuideSkill]:
    """Filter the shared discovery mapping for one session's feature flags."""
    return {
        name: skill for name, skill in discovered.items() if check_frontmatter_requirements(skill.requirements, flags)
    }


async def _discover_guide_skills(session: Any, resolver: Any) -> dict[str, GuideSkill]:
    """Discover effective skills from one session and document resolver."""
    skills_dir = resolver(SKILLS_DIR)

    async def _max_file_mtime(base: Path, fallback: float) -> float:
        result = fallback
        async for candidate in AsyncPath(base).rglob("*"):
            if await candidate.is_file():
                try:
                    result = max(result, (await candidate.stat()).st_mtime)
                except OSError:
                    continue
        return result

    flags = await resolve_all_flags(session)
    runtime = get_runtime()
    development_mode = is_value_true(flags.get(FLAG_GUIDE_DEVELOPMENT))

    async with runtime.skill_discovery_lock:
        cached = runtime.skill_discovery_cache
        if not development_mode and cached is not None and time.monotonic() < cached[1] + 300:
            discovered = cached[2]
        else:
            try:
                root_mtime = (await AsyncPath(skills_dir).stat()).st_mtime
                effective_mtime = await _max_file_mtime(skills_dir, root_mtime)
            except OSError as error:
                logger.warning("Retaining cached Guide skill discovery after validation failure: %s", error)
                return {} if cached is None else _visible_guide_skills(cached[2], flags)
            if not development_mode and cached is not None and cached[0] >= effective_mtime:
                discovered = cached[2]
            else:
                try:
                    files = await discover_document_files(skills_dir, ["**/SKILL.md"])
                except OSError as error:
                    logger.warning("Retaining cached Guide skill discovery after refresh failure: %s", error)
                    return {} if cached is None else _visible_guide_skills(cached[2], flags)

                if files.truncation_reasons:
                    logger.warning("Guide skill discovery truncated by %s", ", ".join(sorted(files.truncation_reasons)))

                discovered = {}
                duplicate_names: set[str] = set()
                for file_info in files:
                    try:
                        file_info.resolve(resolver, SKILLS_DIR)
                        frontmatter = parse_content_with_frontmatter(await file_info.read_raw()).frontmatter
                    except (OSError, UnicodeError) as error:
                        logger.warning("Ignoring unreadable Guide skill package %s: %s", file_info.path, error)
                        continue
                    package_root = PurePosixPath(file_info.name).parent
                    name = frontmatter.get("name")
                    description = frontmatter.get("description")
                    usage = frontmatter.get("usage")
                    if package_root == PurePosixPath(".") or not all(
                        isinstance(value, str) and value for value in (name, description, usage)
                    ):
                        logger.warning("Ignoring Guide skill %s without valid catalogue frontmatter", file_info.path)
                        continue
                    assert isinstance(name, str)
                    assert isinstance(description, str)
                    assert isinstance(usage, str)
                    try:
                        validate_content_name(name, "Guide skill")
                    except ValueError as error:
                        logger.warning("Ignoring Guide skill package %s: %s", file_info.path, error)
                        continue
                    skill = GuideSkill(
                        name=name,
                        description=description,
                        usage=usage,
                        frontmatter=MappingProxyType(
                            {key: value for key, value in frontmatter.items() if key != "name"}
                        ),
                        requirements=MappingProxyType(
                            {key: value for key, value in frontmatter.items() if key.startswith("requires-")}
                        ),
                        package_root=package_root,
                    )
                    if name in duplicate_names:
                        continue
                    if existing := discovered.pop(name, None):
                        logger.warning(
                            "Ignoring duplicate Guide skill name %s at %s and %s",
                            name,
                            existing.package_root,
                            skill.package_root,
                        )
                        duplicate_names.add(name)
                        continue
                    discovered[name] = skill
                runtime.cache_skill_discovery(effective_mtime, time.monotonic(), discovered)

    return _visible_guide_skills(discovered, flags)


async def discover_guide_skills(request_context: RequestContext) -> list[GuideSkill]:
    """Discover skills from their frontmatter, excluding unmet requirements."""
    skills = await _discover_guide_skills(request_context.session, request_context.resolve_document_path)
    return [skills[name] for name in sorted(skills)]


async def discover_guide_skills_for_rendering(session: Any, resolver: Any) -> dict[str, str]:
    """Return catalogue descriptions for skill footnotes during rendering."""
    skills = await _discover_guide_skills(session, resolver)
    return {name: skills[name].description for name in sorted(skills)}


def _catalogue_table_cell(value: str) -> str:
    """Normalise arbitrary frontmatter text for a single Markdown table cell."""
    return " ".join(value.split()).replace("|", r"\|")


def _skill_catalogue_content(skills: list[GuideSkill], *, table: bool = False) -> str:
    """Present one separately addressable catalogue item for each skill."""
    if not skills:
        return "No Guide skills are currently available."
    if table:
        rows = ["| Skill | Purpose | Use when | Entrypoint |", "|---|---|---|---|"]
        rows.extend(
            "| "
            f"`{_catalogue_table_cell(skill.name)}` | "
            f"{_catalogue_table_cell(skill.description)} | "
            f"{_catalogue_table_cell(skill.usage)} | "
            f"`{skill.uri}` |"
            for skill in skills
        )
        return "\n".join(rows)
    return "\n\n".join(
        f"### {skill.name}\n\n{skill.description}\n\nUse when: {skill.usage}\n\nEntrypoint: `{skill.uri}`"
        for skill in skills
    )


class ListSkillsArgs(ToolArguments):
    """Arguments for list_skills tool."""

    verbose: bool = Field(
        default=False,
        description="Return a user-facing catalogue instead of agent-only availability information",
    )
    table: bool = Field(
        default=False,
        description="Return the user-facing catalogue as a Markdown table",
    )


async def internal_list_skills(args: ListSkillsArgs, request_context: RequestContext) -> Result[str]:
    """List the Guide-provided skill catalogue with the requested audience."""
    user_facing = args.verbose or args.table
    disposition = USER_INFO if user_facing else AGENT_INFO
    instruction = INSTRUCTION_DISPLAY_ONLY if user_facing else INSTRUCTION_AGENT_INFORMATION
    return Result.ok(
        _skill_catalogue_content(await discover_guide_skills(request_context), table=args.table),
        instruction=instruction,
        disposition=disposition,
    )


@toolfunc(ListSkillsArgs)
async def list_skills(args: ListSkillsArgs, request_context: RequestContext) -> ToolResult:
    """List Guide-provided skills and their explicit entrypoint URIs.

    By default the catalogue is agent information for availability checks. Pass
    ``verbose=true`` for a user-facing catalogue or ``table=true`` for a
    user-facing Markdown table. Select a listed skill and retrieve its
    entrypoint URI before applying that skill's instructions.
    """
    result = await internal_list_skills(args, request_context)
    return await tool_result("list_skills", result, session=request_context.session, session_id=args.session_id)


def _skill_member_path(skill_path: str, skills: Mapping[str, GuideSkill]) -> tuple[GuideSkill, str] | None:
    """Locate a package and its requested literal member path."""
    requested = PurePosixPath(skill_path)
    if requested.is_absolute() or any(part in {".", ".."} for part in requested.parts):
        raise ValueError("Guide skill member path must remain within its package")
    if any(has_magic(part) for part in requested.parts):
        raise ValueError("Guide skill member path must not contain glob syntax")

    if not requested.parts:
        return None
    skill = skills.get(requested.parts[0])
    if skill is None:
        return None
    member_parts = requested.parts[1:]
    return skill, PurePosixPath(*member_parts).as_posix() if member_parts else "SKILL.md"


def _skill_template_context(skill: GuideSkill, kwargs: Mapping[str, Any]) -> TemplateContext:
    """Build public package references for every rendered skill file."""
    defaulted_forms = getattr(kwargs, "defaulted_forms", frozenset())
    return TemplateContext(
        {
            "skill": {
                "path": skill.name,
                "entrypoint": skill.entrypoint_path,
                "uri": skill.uri,
                "resources_uri": f"{skill.uri}/resources",
                "scripts_uri": f"{skill.uri}/scripts",
                "agents_uri": f"{skill.uri}/agents",
            },
            "elicitation": {"defaulted": {form: True for form in defaulted_forms}},
        },
        keyword_context(kwargs),
    )


async def _read_guide_skill(
    skill_path: str,
    request_context: RequestContext,
    *,
    kwargs: Mapping[str, Any] | None = None,
    mcp_context: Context | None = None,
) -> Result[Any] | InputRequiredResult:
    """Render one contained member of a server-owned skill package."""
    try:
        selected = _skill_member_path(
            skill_path,
            await _discover_guide_skills(request_context.session, request_context.resolve_document_path),
        )
    except ValueError as error:
        return Result.failure(str(error), error_type=ERROR_VALIDATION)
    if selected is None:
        return Result.failure(f"Guide skill '{skill_path}' was not found", error_type=ERROR_NOT_FOUND)
    skill, member_path = selected

    rendered_kwargs: Mapping[str, Any] = kwargs or {}
    if member_path == "SKILL.md":
        resolved_kwargs = await resolve_skill_elicitations(skill.frontmatter, rendered_kwargs, mcp_context)
        if isinstance(resolved_kwargs, (Result, InputRequiredResult)):
            return resolved_kwargs
        rendered_kwargs = resolved_kwargs

    template_context = _skill_template_context(skill, rendered_kwargs)

    async def prepare_policy_partials(file_info, context, project_flags):
        return await gather_policy_partials(request_context, file_info, context or TemplateContext({}), project_flags)

    try:
        rendered = await render_content(
            request_context.session,
            f"{skill.package_root.as_posix()}/{member_path}",
            SKILLS_DIR,
            template_context,
            "Guide skills",
            prepare_partials=prepare_policy_partials,
            resolver=request_context.resolve_document_path,
        )
    except FileNotFoundError:
        return Result.failure(f"Guide skill '{skill_path}' was not found", error_type=ERROR_NOT_FOUND)
    except RuntimeError as error:
        return Result.failure(str(error), error_type=ERROR_VALIDATION)
    if rendered is None:
        return Result.failure(f"Guide skill '{skill_path}' is unavailable for this project", error_type=ERROR_NOT_FOUND)
    if rendered.errors:
        rendered.log_discarded_errors(f"Template {rendered.template_path}")
    return Result.ok(
        rendered.content,
        message=f"Rendered skill file: {skill.name}/{member_path}",
        instruction=rendered.instruction,
        disposition=rendered.disposition,
        cache_policy=rendered.cache_policy,
    )


async def internal_use_skill(
    skill_name: str,
    request_context: RequestContext,
    *,
    kwargs: Mapping[str, Any] | None = None,
    mcp_context: Context | None = None,
) -> Result[Any] | InputRequiredResult:
    """Resolve one catalogued Guide skill through its SKILL.md entrypoint."""
    identifier = skill_name.removeprefix("$")
    skills = await _discover_guide_skills(request_context.session, request_context.resolve_document_path)
    selected = skills.get(identifier)
    if selected is None:
        return Result.failure(f"Guide skill '{identifier}' was not found", error_type=ERROR_NOT_FOUND)
    return await _read_guide_skill(selected.name, request_context, kwargs=kwargs, mcp_context=mcp_context)


class UseSkillArgs(ToolArguments):
    """Arguments for the client-facing Guide skill tool."""

    skill: str = Field(
        ...,
        description="Guide skill name, optionally beginning with $. Do not pass a guide:// URI.",
    )
    args: list[str] = Field(
        default_factory=list,
        description="Skill option tokens parsed with Guide's shared option parser, such as ['mode=unrelenting', 'verbose'].",
    )


@toolfunc(UseSkillArgs)
async def use_skill(
    args: UseSkillArgs,
    request_context: RequestContext,
    mcp_context: Context | None = None,
) -> ToolResult | InputRequiredResult:
    """Use a selected Guide skill by name, parsing options through the shared Guide parser."""
    kwargs, _, parse_errors = parse_command_arguments([args.skill, *args.args], bare_tokens_are_flags=True)
    if parse_errors:
        return await tool_result(
            "use_skill",
            Result.failure(f"Skill argument parsing failed: {'; '.join(parse_errors)}", error_type=ERROR_VALIDATION),
            session=request_context.session,
            session_id=args.session_id,
        )
    result = await internal_use_skill(
        args.skill,
        request_context,
        kwargs=kwargs,
        mcp_context=mcp_context,
    )
    if isinstance(result, InputRequiredResult):
        return result
    return await tool_result("use_skill", result, session=request_context.session, session_id=args.session_id)


def session_id_from_guide_uri(uri: str) -> str | None:
    """Return the optional reserved session ID without interpreting it."""
    values = parse_qs(urlsplit(uri).query, keep_blank_values=True).get("session_id")
    if not values:
        return None
    if len(values) != 1:
        raise ValueError("Resource URI must contain at most one session_id value")
    return values[0]


class ReadResourceArgs(ToolArguments):
    """Arguments for read_resource tool."""

    uri: str = Field(
        ...,
        description=(
            "A guide:// URI to resolve. "
            "Content URIs (guide://expression/pattern) return category or collection content. "
            "Command URIs (guide://_command/args?kwargs) execute server commands. "
            "Skill URIs (guide://$ or guide://$skill/path) return the skills catalogue or a skill instruction. "
            "A unique ?session_id= query value is copied onto the session_id argument when "
            "that argument is omitted."
        ),
    )

    @model_validator(mode="after")
    def apply_uri_session_id(self) -> "ReadResourceArgs":
        """Copy a unique URI session_id onto the tool field when it is absent."""
        uri_session_id = session_id_from_guide_uri(self.uri)
        if uri_session_id is not None:
            if not uri_session_id:
                raise ValueError("Resource URI session_id must be non-empty")
            if self.session_id is None:
                self.session_id = uri_session_id
        return self


async def internal_read_resource(
    args: ReadResourceArgs, request_context: RequestContext, *, mcp_context: Context | None = None
) -> Result[Any] | InputRequiredResult:
    """Resolve a guide:// URI and return its content or command output.

    Args:
        args: Tool arguments with URI
        request_context: Resolved application request context

    Returns:
        Result containing resolved content or command output
    """
    try:
        parsed = parse_guide_uri(args.uri)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_VALIDATION)

    if parsed.is_command:
        session = request_context.session
        try:
            commands_dir = request_context.resolve_document_path(COMMANDS_DIR)
            commands = await discover_commands(commands_dir, session)
            command_names: list[str] = [cmd["name"] for cmd in commands]
            for cmd in commands:
                command_names.extend(cmd.get("aliases", []))
                command_names.extend(alias["path"] for alias in normalise_alias_metadata(cmd.get("alias_metadata", [])))
            parsed = parse_guide_uri(args.uri, command_names)
        except ValueError as e:
            return Result.failure(str(e), error_type=ERROR_VALIDATION)

        # Lazy import avoids a circular import: guide_prompt imports tool modules
        # during prompt setup, while command URI resolution needs handle_command.
        from mcp_guide.prompts.guide_prompt import handle_command

        return await handle_command(
            parsed.expression,
            kwargs=dict(parsed.kwargs),
            args=list(parsed.args),
            request_context=request_context,
        )

    if parsed.is_skill:
        if not parsed.expression:
            try:
                list_args = ListSkillsArgs.model_validate({**parsed.kwargs, "session_id": args.session_id})
            except ValidationError as error:
                return Result.failure(str(error), error_type=ERROR_VALIDATION)
            return await internal_list_skills(list_args, request_context)
        return await _read_guide_skill(
            parsed.expression,
            request_context,
            kwargs=parsed.kwargs,
            mcp_context=mcp_context,
        )

    content_args = ContentArgs(
        expression=parsed.expression,
        pattern=parsed.pattern,
        force=False,
        session_id=request_context.session_id,
    )
    return await internal_get_content(content_args, request_context)


@toolfunc(ReadResourceArgs)
async def read_resource(
    args: ReadResourceArgs,
    request_context: RequestContext,
    mcp_context: Context | None = None,
) -> ToolResult | InputRequiredResult:
    """Resolve a guide:// URI and return its content or command output.

    Accepts content URIs (guide://expression/pattern) to retrieve category or collection
    content, command URIs (guide://_command) to execute server commands, and skill URIs
    (guide://$ or guide://$skill/path) to retrieve Guide-provided skills. A unique
    session_id on the URI query is used when the sibling session_id argument is omitted.
    """
    result = await internal_read_resource(args, request_context, mcp_context=mcp_context)
    if isinstance(result, InputRequiredResult):
        return result
    return await tool_result("read_resource", result, session=request_context.session, session_id=args.session_id)
