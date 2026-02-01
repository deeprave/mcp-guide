"""Content rendering."""

from collections.abc import Awaitable
from pathlib import Path
from typing import Callable, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.discovery.files import FileInfo, discover_category_files
from mcp_guide.models import resolve_all_flags
from mcp_guide.render.content import RenderedContent
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.template import render_template
from mcp_guide.session import get_current_session, get_or_create_session

logger = get_logger(__name__)


async def discover_single_file(
    category_path: Path,
    pattern: str,
    docroot: Path,
    display_name: str,
) -> list[FileInfo]:
    """Discover single file matching pattern, raising error if multiple or none found."""
    files = await discover_category_files(category_path, [pattern])

    if not files:
        raise FileNotFoundError(f"No template found matching pattern '{pattern}' in {display_name}")

    if len(files) > 1:
        file_paths = [str(f.path) for f in files]
        raise FileNotFoundError(f"Multiple templates found matching pattern '{pattern}': {file_paths}")

    file_info = files[0]
    file_info.resolve(category_path, docroot)
    return [file_info]


async def render_content(
    pattern: str,
    category_dir: str,
    extra_context: Optional[TemplateContext] = None,
    category_name: Optional[str] = None,
    discover_files: Optional[Callable[[Path, str, Path, str], Awaitable[list[FileInfo]]]] = None,
    process_context: Optional[Callable[[TemplateContext, FileInfo], Awaitable[TemplateContext]]] = None,
) -> RenderedContent | None:
    """Render template from category directory matching pattern.

    Args:
        pattern: Glob pattern to match template file
        category_dir: Directory name relative to docroot (e.g., "_workflow", "_openspec")
        extra_context: Optional additional context to layer on top
        category_name: Optional category name for error messages (defaults to category_dir)
        discover_files: Optional function to discover files (defaults to single-file discovery)
        process_context: Optional function to process context before rendering

    Returns:
        RenderedContent with content and frontmatter, or None if filtered by requires-*
        or if an error occurs during rendering

    Raises:
        FileNotFoundError: No template matches pattern or multiple matches found (default behavior)
    """
    session = await get_or_create_session()
    docroot = Path(await session.get_docroot())
    category_path = docroot / category_dir
    display_name = category_name or category_dir

    # Use provided discovery function or default to single-file
    if discover_files is None:
        files = await discover_single_file(category_path, pattern, docroot, display_name)
    else:
        files = await discover_files(category_path, pattern, docroot, display_name)

    current_session = get_current_session()
    requirements_context = await resolve_all_flags(current_session)  # type: ignore[arg-type]

    # Process context if callback provided (augments extra_context)
    context = extra_context
    if process_context is not None:
        context = await process_context(extra_context or TemplateContext({}), files[0])

    try:
        rendered = await render_template(
            file_info=files[0],
            base_dir=files[0].path.parent,
            project_flags=requirements_context,
            context=context,
        )
    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
        logger.error(f"Failed to read {display_name} template {pattern}: {e}")
        return None
    except Exception as e:
        # Broad catch is intentional - gracefully handle any rendering errors
        # Full traceback is logged for debugging
        logger.exception(f"Unexpected error rendering {display_name} template {pattern}")
        return None

    if rendered is None:
        logger.debug(f"Template {files[0].path} filtered by requires-* directives")
        return None

    return rendered
