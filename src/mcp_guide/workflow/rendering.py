"""Workflow template rendering utilities."""

from typing import Optional

from mcp_guide.config_constants import WORKFLOW_DIR
from mcp_guide.render.content import RenderedContent
from mcp_guide.render.rendering import render_content
from mcp_guide.utils.template_context import TemplateContext


async def render_workflow_template(
    template_pattern: str, extra_context: Optional[TemplateContext] = None
) -> RenderedContent | None:
    """Render workflow template.

    Returns:
        RenderedContent with content and frontmatter, or None if filtered by requires-*
    """
    return await render_content(template_pattern, WORKFLOW_DIR, extra_context)
