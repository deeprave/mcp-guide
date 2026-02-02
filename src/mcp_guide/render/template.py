"""Template rendering implementation."""

from pathlib import Path
from typing import Any, Dict, Optional

from mcp_guide.core.file_reader import read_file_content
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.cache import get_template_contexts
from mcp_guide.render.content import FM_INCLUDES, FM_REQUIRES_PREFIX, RenderedContent
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.frontmatter import _check_requires_directive, parse_content_with_frontmatter
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
    parsed = parse_content_with_frontmatter(content)

    # Check requires-* directives
    for key in parsed.frontmatter.keys():
        if not key.startswith(FM_REQUIRES_PREFIX):
            continue

        flag_name = key[len(FM_REQUIRES_PREFIX) :]
        required_value = parsed.frontmatter[key]
        flag_value = project_flags.get(flag_name)

        if not _check_requires_directive(required_value, flag_value):
            logger.debug(f"Template {file_info.path} filtered: {key} not met")
            return None

    # Build context: base → frontmatter vars → caller
    base_context = await get_template_contexts()

    # Extract frontmatter vars (exclude requires-* and includes)
    frontmatter_vars = {
        k: v for k, v in parsed.frontmatter.items() if not k.startswith(FM_REQUIRES_PREFIX) and k != FM_INCLUDES
    }

    final_context = base_context
    if frontmatter_vars:
        final_context = final_context.new_child(frontmatter_vars)
    if context:
        final_context = final_context.new_child(context)

    # Render template or return as-is
    if is_template_file(file_info):
        result = await render_template_content(
            content=parsed.content,
            context=final_context,
            file_path=str(file_info.path),
            metadata=dict(parsed.frontmatter),
            base_dir=base_dir,
        )
        if not result.success:
            # Raise exception with detailed error context
            raise RuntimeError(f"Template rendering failed: {result.error}")
        assert result.value is not None, "Result value should not be None when success is True"
        rendered_content = result.value
    else:
        rendered_content = parsed.content

    return RenderedContent(
        frontmatter=parsed.frontmatter,
        frontmatter_length=parsed.frontmatter_length,
        content=rendered_content,
        content_length=len(rendered_content),
        template_path=file_info.path,
        template_name=file_info.path.name,
    )
