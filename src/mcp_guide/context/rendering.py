"""Context template rendering utilities."""

from pathlib import Path
from typing import Any, Optional

from mcp_guide.session import get_or_create_session
from mcp_guide.utils.system_content import render_system_content
from mcp_guide.utils.template_context_cache import get_template_contexts

COMMON_DIR = "_common"


async def render_context_template(template_pattern: str, extra_context: Optional[dict[str, Any]] = None) -> str:
    """Render context template from _common/ directory.

    Args:
        template_pattern: Pattern to match template file
        extra_context: Optional additional context to layer on top

    Returns:
        Rendered template content

    Raises:
        Exception: If template rendering fails
    """
    session = await get_or_create_session()
    docroot = Path(await session.get_docroot())
    common_dir = docroot / COMMON_DIR

    context = await get_template_contexts()
    if extra_context:
        context = context.new_child(extra_context)

    result = await render_system_content(
        system_dir=common_dir, pattern=template_pattern, context=context, docroot=docroot
    )

    if not result.success or not result.value:
        raise Exception(f"Failed to render template: {result.error}")

    return result.value
