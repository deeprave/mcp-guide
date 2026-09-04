"""Content rendering."""

from collections.abc import Awaitable
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.discovery.files import FileInfo, discover_document_files
from mcp_guide.models import resolve_all_flags
from mcp_guide.render.content import RenderedContent
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.template import render_template

if TYPE_CHECKING:
    from mcp_guide.session import Session

logger = get_logger(__name__)


async def discover_single_file(
    resolver: Callable[[str | Path], Path],
    category_dir: str,
    pattern: str,
    display_name: str,
) -> list[FileInfo]:
    """Discover a single file matching pattern, raising an error if multiple or none found."""
    category_path = resolver(category_dir)
    files = await discover_document_files(category_path, [pattern])

    if not files:
        raise FileNotFoundError(f"No template found matching pattern '{pattern}' in {display_name}")

    if len(files) > 1:
        file_paths = [str(f.path) for f in files]
        raise FileNotFoundError(f"Multiple templates found matching pattern '{pattern}': {file_paths}")

    file_info = files[0]
    file_info.resolve(resolver, category_dir)
    return [file_info]


async def render_content(
    session: "Session",
    pattern: str,
    category_dir: str,
    extra_context: Optional[TemplateContext] = None,
    category_name: Optional[str] = None,
    discover_files: Optional[Callable[[Callable[[str | Path], Path], str, str, str], Awaitable[list[FileInfo]]]] = None,
    process_context: Optional[Callable[[TemplateContext, FileInfo], Awaitable[TemplateContext]]] = None,
    *,
    resolver: Callable[[str | Path], Path] | None = None,
) -> RenderedContent | None:
    """Render template from the category directory matching pattern.

    Args:
        pattern: Glob pattern to match a template file
        category_dir: Directory name relative to docroot (e.g. "_workflow", "_openspec")
        extra_context: Optional additional context to layer on top
        category_name: Optional category name for error messages (defaults to category_dir)
        discover_files: Optional function to discover files (defaults to single-file discovery)
        process_context: Optional function to process context before rendering
        resolver: Document-path resolver. Request paths must pass the captured
            RequestContext resolver. When omitted, the process runtime resolver
            is used (background listeners and tasks).

    Returns:
        RenderedContent with content and frontmatter, or None if filtered by requires-*
        or if an error occurs during rendering

    Raises:
        FileNotFoundError: No template matches pattern or multiple matches found (default behaviour)
    """
    if session is None:
        raise RuntimeError("Content rendering requires an explicit Session")
    if resolver is None:
        from mcp_guide.runtime import get_runtime

        resolver = await get_runtime().get_docroot_resolver()
    display_name = category_name or category_dir

    # Use the provided discovery function or default to single-file
    if discover_files is None:
        files = await discover_single_file(resolver, category_dir, pattern, display_name)
    else:
        files = await discover_files(resolver, category_dir, pattern, display_name)

    requirements_context = await resolve_all_flags(session)

    # Process context if callback provided (augments extra_context)
    context = extra_context
    if process_context is not None:
        context = await process_context(extra_context or TemplateContext({}), files[0])

    # noinspection PyBroadException
    try:
        rendered = await render_template(
            session,
            file_info=files[0],
            base_dir=files[0].path.parent,
            project_flags=requirements_context,
            context=context,
        )
    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
        logger.error(f"Failed to read {display_name} template {pattern}: {e}")
        return None
    except Exception:
        # Broad catch is intentional - gracefully handle any rendering errors
        # Full traceback is logged for debugging
        logger.exception(f"Unexpected error rendering {display_name} template {pattern}")
        return None

    if rendered is None:
        logger.debug(f"Template {files[0].path} filtered by requires-* directives")
        return None

    if rendered.errors:
        rendered.log_discarded_errors(f"Template {files[0].path}")

    return rendered
