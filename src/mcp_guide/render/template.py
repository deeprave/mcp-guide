"""Template rendering implementation."""

from pathlib import Path
from typing import Any, Dict, Optional

from mcp_guide.core.file_reader import read_file_content
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.cache import get_template_contexts
from mcp_guide.render.content import FM_INCLUDES, FM_REQUIRES_PREFIX, RenderedContent
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.renderer import is_template_file, render_template_content

logger = get_logger(__name__)


async def render_template(
    file_info: FileInfo,
    base_dir: Path,
    project_flags: Dict[str, Any],
    context: Optional[TemplateContext] = None,
) -> Optional[RenderedContent]:
    """Render a template file with frontmatter and context.

    Args:
        file_info: File information for the template
        base_dir: Base directory for template resolution
        project_flags: Project feature flags for requires-* checking
        context: Optional caller-provided context

    Returns:
        RenderedContent if successful, None if filtered by requires-*

    Raises:
        RuntimeError: If template rendering fails
        Exception: Other errors during processing
    """
    content = await read_file_content(file_info.path)

    # Build context for frontmatter field rendering
    base_context = await get_template_contexts()

    # Extract frontmatter vars will be done after processing
    # Build final context: base → caller
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

    if frontmatter_vars:
        final_context = base_context.new_child(frontmatter_vars)
        if context:
            final_context = final_context.new_child(context)
    # Render template or return as-is
    partial_frontmatter_list: list[Dict[str, Any]] = []
    if is_template_file(file_info):
        result = await render_template_content(
            content=processed.content,
            context=final_context,
            file_path=str(file_info.path),
            metadata=dict(processed.frontmatter),
            base_dir=base_dir,
        )
        if not result.success:
            # Raise exception with detailed error context
            raise RuntimeError(f"Template rendering failed: {result.error}")
        assert result.value is not None, "Result value should not be None when success is True"
        rendered_content, partial_frontmatter_list = result.value
    else:
        rendered_content = processed.content

    return RenderedContent(
        frontmatter=processed.frontmatter,
        frontmatter_length=processed.frontmatter_length,
        content=rendered_content,
        content_length=len(rendered_content),
        template_path=file_info.path,
        template_name=file_info.path.name,
        partial_frontmatter=partial_frontmatter_list,
    )
