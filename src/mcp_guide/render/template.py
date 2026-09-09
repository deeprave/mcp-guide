"""Template rendering implementation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from mcp_guide.content_limits import DEFAULT_MAX_CONTENT_LIMIT, ensure_within_limit
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.cache import get_template_contexts
from mcp_guide.render.content import FM_INCLUDES, FM_REQUIRES_PREFIX, RenderedContent
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.renderer import is_template_file, render_template_content

if TYPE_CHECKING:
    from mcp_guide.render.cache_policy import CachePolicy
    from mcp_guide.session import Session

logger = get_logger(__name__)


async def render_template(
    session: "Session",
    file_info: FileInfo,
    base_dir: Path,
    project_flags: Dict[str, Any],
    context: Optional[TemplateContext] = None,
    pre_partials: Optional[Dict[str, str]] = None,
    pre_partial_frontmatter: Optional[Dict[str, list[Dict[str, Any]]]] = None,
    pre_partial_cache_policies: Optional[Dict[str, list[CachePolicy]]] = None,
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
            base_dir=base_dir,
            resolver=resolver,
            partials=pre_partials,
            pre_rendered_partial_frontmatter=pre_partial_frontmatter,
            pre_rendered_partial_cache_policies=pre_partial_cache_policies,
            max_content_limit=max_content_limit,
        )
        if not result.success:
            raise RuntimeError(f"Template rendering failed: {result.error}")
        assert result.value is not None, "Result value should not be None when success is True"
        rendered_content, partial_frontmatter_list, partial_cache_policies, template_errors = result.value
    else:
        rendered_content = processed.content
        partial_frontmatter_list = []
        partial_cache_policies = []
        template_errors = []

    ensure_within_limit(len(rendered_content.encode("utf-8")), limit_name="max-content-limit", limit=max_content_limit)
    return RenderedContent(
        frontmatter=processed.frontmatter,
        frontmatter_length=processed.frontmatter_length,
        content=rendered_content,
        content_length=len(rendered_content),
        template_path=file_info.path,
        template_name=file_info.path.name,
        partial_frontmatter=partial_frontmatter_list,
        partial_cache_policies=partial_cache_policies,
        errors=template_errors,
    )
