"""Workflow template rendering utilities."""

from typing import TYPE_CHECKING, Optional

from mcp_guide.config_constants import WORKFLOW_DIR
from mcp_guide.render.content import RenderedContent
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.rendering import render_content

if TYPE_CHECKING:
    from mcp_guide.session import Session


async def render_workflow_template(
    session: "Session", template_pattern: str, extra_context: Optional[TemplateContext] = None
) -> RenderedContent | None:
    """Render workflow template.

    Returns:
        RenderedContent with content and frontmatter, or None if filtered by requires-*
    """
    return await render_content(session, template_pattern, WORKFLOW_DIR, extra_context)
