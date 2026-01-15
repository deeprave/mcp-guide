"""Workflow template rendering utilities."""

from pathlib import Path
from typing import Any, Optional

from mcp_guide.session import get_or_create_session
from mcp_guide.utils.system_content import render_system_content
from mcp_guide.utils.template_context_cache import get_template_contexts
from mcp_guide.workflow.constants import WORKFLOW_DIR

COMMON_DIR = "_common"


async def render_workflow_template(template_pattern: str) -> str:
    """Render workflow template."""
    session = await get_or_create_session()
    docroot = Path(await session.get_docroot())
    workflow_dir = docroot / WORKFLOW_DIR
    context = await get_template_contexts()

    result = await render_system_content(
        system_dir=workflow_dir, pattern=template_pattern, context=context, docroot=docroot
    )

    if not result.success or not result.value:
        raise Exception(f"Failed to render template: {result.error}")

    return result.value


async def render_common_template(template_pattern: str, extra_context: Optional[dict[str, Any]] = None) -> str:
    """Render common template."""
    session = await get_or_create_session()
    docroot = Path(await session.get_docroot())
    common_dir = docroot / COMMON_DIR

    if extra_context:
        from mcp_guide.utils.template_context import TemplateContext

        base_context = await get_template_contexts()
        # Create new context with extra_context layered on top of base_context
        all_maps = [extra_context] + [dict(m) for m in base_context.maps]
        context = TemplateContext(*all_maps)
    else:
        context = await get_template_contexts()

    result = await render_system_content(
        system_dir=common_dir, pattern=template_pattern, context=context, docroot=docroot
    )

    if not result.success or not result.value:
        raise Exception(f"Failed to render template: {result.error}")

    return result.value
