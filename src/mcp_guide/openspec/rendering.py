"""OpenSpec template rendering utilities."""

from typing import Optional

from mcp_guide.config_constants import OPENSPEC_DIR
from mcp_guide.render.content import RenderedContent
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.rendering import render_content


async def render_openspec_template(
    template_pattern: str, extra_context: Optional[TemplateContext] = None
) -> RenderedContent | None:
    """Render OpenSpec template.

    Args:
        template_pattern: Pattern to match template file
        extra_context: Optional additional context to layer on top

    Returns:
        RenderedContent with content and frontmatter, or None if filtered by requires-*

    Note:
        Template injection is not a concern - Mustache templates are safe by design
        (no code execution, automatic HTML escaping). Type safety is enforced by mypy.
    """
    return await render_content(template_pattern, OPENSPEC_DIR, extra_context)
