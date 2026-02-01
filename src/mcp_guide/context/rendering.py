"""Context template rendering utilities."""

from typing import Any, Optional

from mcp_guide.config_constants import CONTEXT_DIR
from mcp_guide.render.content import RenderedContent
from mcp_guide.render.rendering import render_content
from mcp_guide.utils.template_context import TemplateContext


async def render_context_template(
    template_pattern: str, extra_context: Optional[dict[str, Any]] = None
) -> RenderedContent | None:
    """Render context template from _context/ directory.

    Args:
        template_pattern: Pattern to match template file
        extra_context: Optional additional context to layer on top

    Returns:
        RenderedContent if successful, None if filtered by requires-*
    """
    context = TemplateContext(extra_context) if extra_context else None
    return await render_content(
        pattern=template_pattern,
        category_dir=CONTEXT_DIR,
        extra_context=context,
        category_name="context",
    )
