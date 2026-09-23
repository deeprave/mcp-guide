"""Template rendering implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from mcp_guide.config_constants import COMMANDS_DIR
from mcp_guide.content_limits import DEFAULT_MAX_CONTENT_LIMIT, ensure_within_limit
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_decorator import get_tool_prefix, get_tool_registration
from mcp_guide.discovery.commands import discover_commands
from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.cache import get_template_contexts
from mcp_guide.render.content import FM_INCLUDES, FM_REQUIRES_PREFIX, RenderedContent
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.document_properties import DocumentContribution
from mcp_guide.render.recommendations import Recommendation
from mcp_guide.render.renderer import is_template_file, render_template_content

if TYPE_CHECKING:
    from mcp_guide.session import Session

logger = get_logger(__name__)


async def _recommendation_footnotes(
    recommendations: list[Recommendation], session: "Session | None", resolver: Callable[[str | Path], Path] | None
) -> str:
    """Append compact, type-specific recommendation footnotes to a document."""
    if not recommendations:
        return ""

    descriptions: dict[str, str] = {}
    commands: set[str] = set()
    content_names: set[str] = set()
    if session is not None and resolver is not None:
        # This local import keeps rendering independent of the tool registration module.
        from mcp_guide.tools.tool_resource import discover_guide_skills_for_rendering

        descriptions = await discover_guide_skills_for_rendering(session, resolver)
        commands = {command["name"] for command in await discover_commands(resolver(COMMANDS_DIR), session)}
        project = await session.get_project()
        content_names = set(project.categories) | set(project.collections)

    footnotes: list[str] = []
    for recommendation in recommendations:
        kind, value = recommendation.kind, recommendation.name
        if kind == "skill":
            if session is not None and value not in descriptions:
                raise ValueError(f"Unknown recommended skill: {value}")
            item = {
                "type": kind,
                "name": value,
                "description": descriptions.get(value, ""),
                "uri": f"guide://${value}",
                "tool": f'{get_tool_prefix()}use_skill("{value}")',
            }
        elif kind == "command":
            if session is not None and value not in commands:
                raise ValueError(f"Unknown recommended command: {value}")
            item = {"type": kind, "name": value, "uri": f"guide://_{value}"}
        elif kind == "tool":
            if get_tool_registration(value) is None:
                raise ValueError(f"Unknown recommended tool: {value}")
            item = {"type": kind, "name": value, "tool": f"{get_tool_prefix()}{value}"}
        else:
            content_name = value.split("/", 1)[0].split(",", 1)[0]
            if session is not None and content_name not in content_names:
                raise ValueError(f"Unknown recommended content: {value}")
            item = {
                "type": "content",
                "name": value,
                "uri": f"guide://{value}",
                "tool": f'{get_tool_prefix()}get_content("{value}")',
            }
        footnotes.append(
            f"[^{recommendation.label}]:\n    ```json\n    {json.dumps(item, separators=(',', ':'))}\n    ```"
        )
    return "\n\n" + "\n\n".join(footnotes)


async def render_template(
    session: "Session | None",
    file_info: FileInfo,
    base_dir: Path,
    project_flags: Dict[str, Any],
    context: Optional[TemplateContext] = None,
    pre_partials: Optional[Dict[str, str]] = None,
    pre_partial_contributions: Optional[Dict[str, list[DocumentContribution]]] = None,
    resolver: Callable[[str | Path], Path] | None = None,
    max_content_limit: int = DEFAULT_MAX_CONTENT_LIMIT,
) -> Optional[RenderedContent]:
    """Render a template file with frontmatter and context.

    Args:
        file_info: File information for the template
        base_dir: Base directory for template resolution
        project_flags: Project feature flags for requires-* checking
        context: Optional caller-provided context
        resolver: Server-side document-root resolver for filesystem partials

    Returns:
        RenderedContent if successful, None if filtered by requires-*

    Raises:
        RuntimeError: If template rendering fails
        Exception: Other errors during processing
    """
    content = await file_info.read_raw(max_bytes=max_content_limit)

    # Build context for frontmatter field rendering
    base_context = await get_template_contexts(session)

    # Build initial context for rendering frontmatter instruction/description fields
    # Frontmatter vars will be added after processing
    final_context = base_context
    if context:
        final_context = final_context.new_child(context)
    # Process frontmatter: parse, check requirements, render instruction/description
    from mcp_guide.render.frontmatter import process_frontmatter

    processed = await process_frontmatter(content, project_flags, final_context)
    if processed is None:
        logger.debug(f"Template {file_info.path} filtered by requirements")
        return None

    # Extract frontmatter vars (exclude requires-* and includes) and add to context
    frontmatter_vars = {
        k: v for k, v in processed.frontmatter.items() if not k.startswith(FM_REQUIRES_PREFIX) and k != FM_INCLUDES
    }

    # Add frontmatter vars to context for template body rendering
    # Context chain: base → caller → frontmatter_vars
    if frontmatter_vars:
        final_context = final_context.new_child(frontmatter_vars)
    # Render template or return as-is
    if is_template_file(file_info):
        result = await render_template_content(
            content=processed.content,
            context=final_context,
            file_path=str(file_info.path),
            metadata=dict(processed.frontmatter),
            requirements_context=project_flags,
            base_dir=base_dir,
            resolver=resolver,
            recommendation_footnotes=lambda items: _recommendation_footnotes(items, session, resolver),
            partials=pre_partials,
            pre_rendered_partial_contributions=pre_partial_contributions,
            max_content_limit=max_content_limit,
        )
        if not result.success:
            raise RuntimeError(f"Template rendering failed: {result.error}")
        assert result.value is not None, "Result value should not be None when success is True"
        rendered_result = result.value
        rendered_content = rendered_result.content
        partial_contributions = rendered_result.partial_contributions
        template_errors = rendered_result.errors
    else:
        rendered_content = processed.content
        partial_contributions = []
        template_errors = []

    ensure_within_limit(len(rendered_content.encode("utf-8")), limit_name="max-content-limit", limit=max_content_limit)
    return RenderedContent(
        frontmatter=processed.frontmatter,
        frontmatter_length=processed.frontmatter_length,
        content=rendered_content,
        content_length=len(rendered_content),
        template_path=file_info.path,
        template_name=file_info.path.name,
        partial_contributions=partial_contributions,
        errors=template_errors,
    )
