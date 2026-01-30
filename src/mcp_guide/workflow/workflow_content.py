"""Workflow template content rendering."""

from pathlib import Path
from typing import TYPE_CHECKING

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.models import resolve_all_flags
from mcp_guide.render.template import render_template
from mcp_guide.session import get_current_session
from mcp_guide.utils.file_discovery import discover_category_files

if TYPE_CHECKING:
    from mcp_guide.utils.template_context import TemplateContext

logger = get_logger(__name__)


async def render_workflow_content(
    pattern: str,
    workflow_dir: Path,
    context: "TemplateContext",
    docroot: Path,
) -> str | None:
    """Render workflow template matching pattern.

    Discovers and renders a single template file from workflow_dir
    matching the given glob pattern.

    Args:
        pattern: Glob pattern to match template file (e.g., "monitoring-*")
        workflow_dir: Directory containing workflow templates (_workflow/)
        context: Template context for rendering
        docroot: Project docroot for partial resolution

    Returns:
        Rendered template content as string, or None if filtered by requires-*
        or if an error occurs during rendering

    Raises:
        FileNotFoundError: No template matches pattern or multiple matches found
    """
    # Discover files matching pattern
    files = await discover_category_files(workflow_dir, [pattern])

    if not files:
        raise FileNotFoundError(f"No template found matching pattern '{pattern}' in {workflow_dir}")

    if len(files) > 1:
        file_paths = [str(f.path) for f in files]
        raise FileNotFoundError(f"Multiple templates found matching pattern '{pattern}': {file_paths}")

    file_info = files[0]

    # Resolve relative path to absolute path
    file_info.resolve(workflow_dir, docroot)

    # Get resolved flags for requires-* checking
    current_session = get_current_session()
    requirements_context = await resolve_all_flags(current_session)  # type: ignore[arg-type]

    # Render template using unified API
    try:
        rendered = await render_template(
            file_info=file_info,
            base_dir=file_info.path.parent,  # Use template's parent for partial resolution
            project_flags=requirements_context,
            context=context,
            docroot=docroot,
        )
    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
        # File I/O errors
        logger.error(f"Failed to read workflow template {pattern}: {e}")
        return None
    except Exception as e:
        # Unexpected errors - log with full traceback
        logger.exception(f"Unexpected error rendering workflow template {pattern}")
        return None

    if rendered is None:
        # Template filtered by requires-* - return None to indicate not applicable
        logger.debug(f"Template {file_info.path} filtered by requires-* directives")
        return None

    return rendered.content
