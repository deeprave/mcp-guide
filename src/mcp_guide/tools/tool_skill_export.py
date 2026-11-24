"""Export rendered Guide skill packages as MIME documents."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from stat import S_IMODE

import yaml
from fastmcp import Context
from mcp_types import InputRequiredResult
from pydantic import Field

from mcp_guide.config_constants import SKILLS_DIR
from mcp_guide.content.formatters.mime import MimeFormatter
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.discovery.files import TEMPLATE_EXTENSIONS, FileInfo
from mcp_guide.models.project import Category
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_NOT_FOUND, ERROR_VALIDATION, make_no_project_result
from mcp_guide.runtime import RequestContext
from mcp_guide.tools.tool_resource import _discover_guide_skills, _read_guide_skill
from mcp_guide.tools.tool_result import ToolResult, tool_result


class ExportSkillArgs(ToolArguments):
    """Arguments for exporting one eligible Guide skill package."""

    skill: str = Field(
        ...,
        description="Guide skill name, optionally beginning with $. Do not pass a guide:// URI or a path.",
    )


def _entrypoint_content(name: str, description: str, usage: str, body: str) -> str:
    """Add the portable Agent Skills metadata to a rendered entrypoint."""
    frontmatter = yaml.safe_dump(
        {"name": name, "description": description, "usage": usage},
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).rstrip()
    return f"---\n{frontmatter}\n---\n{body}"


async def _package_files(
    skill_name: str,
    request_context: RequestContext,
    mcp_context: Context | None,
) -> Result[list[FileInfo]] | InputRequiredResult:
    """Render every regular file in one selected skill package."""
    skill_name = skill_name.removeprefix("$")
    skills = await _discover_guide_skills(request_context.session, request_context.resolve_document_path)
    skill = skills.get(skill_name)
    if skill is None:
        return Result.failure(f"Guide skill '{skill_name}' was not found", error_type=ERROR_NOT_FOUND)

    skills_root = request_context.resolve_document_path(SKILLS_DIR)
    package_root = skills_root / skill.package_root
    try:
        members = sorted(path for path in package_root.rglob("*") if path.is_file())
    except OSError as error:
        return Result.failure(str(error), error_type=ERROR_VALIDATION)

    category = Category(dir="", patterns=["**/*"], name="skills")
    package_files: list[FileInfo] = []
    for member in members:
        member_path = member.relative_to(package_root).as_posix()
        for extension in TEMPLATE_EXTENSIONS:
            if member_path.endswith(extension):
                member_path = member_path[: -len(extension)]
                break
        rendered = await _read_guide_skill(f"{skill.name}/{member_path}", request_context, mcp_context=mcp_context)
        if isinstance(rendered, InputRequiredResult):
            return rendered
        if not rendered.success:
            return rendered
        content = rendered.value
        if not isinstance(content, str):
            return Result.failure(f"Guide skill '{member_path}' did not render text", error_type=ERROR_VALIDATION)
        if member_path == "SKILL.md":
            content = _entrypoint_content(skill.name, skill.description, skill.usage, content)
        stat_result = member.stat()
        package_files.append(
            FileInfo(
                path=Path(skill.name) / member_path,
                name=f"{skill.name}/{member_path}",
                size=len(content.encode("utf-8")),
                content_size=len(content.encode("utf-8")),
                mtime=datetime.fromtimestamp(stat_result.st_mtime),
                content=content,
                category=category,
                mode=S_IMODE(stat_result.st_mode),
            )
        )
    return Result.ok(package_files)


@toolfunc(ExportSkillArgs)
async def export_skill(
    args: ExportSkillArgs,
    request_context: RequestContext,
    mcp_context: Context | None = None,
) -> ToolResult | InputRequiredResult:
    """Return one eligible rendered skill package as MIME documents for local export."""
    if not request_context.is_bound:
        return await tool_result(
            "export_skill", await make_no_project_result(), session=request_context.session, session_id=args.session_id
        )
    files = await _package_files(args.skill, request_context, mcp_context)
    if isinstance(files, InputRequiredResult):
        return files
    if not files.success:
        return await tool_result("export_skill", files, session=request_context.session, session_id=args.session_id)
    assert files.value is not None
    content = await MimeFormatter().format(files.value, request_context.resolve_document_path)
    return await tool_result(
        "export_skill", Result.ok(content), session=request_context.session, session_id=args.session_id
    )
