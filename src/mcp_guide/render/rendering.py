"""Content rendering."""

from collections.abc import Awaitable
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.discovery.files import FileInfo, discover_document_files
from mcp_guide.models import resolve_all_flags
from mcp_guide.render.content import RenderedContent
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.document_properties import DocumentContribution
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

    if files.truncation_reasons:
        raise FileNotFoundError(f"Template discovery was truncated matching pattern '{pattern}' in {display_name}")

    if not files:
        raise FileNotFoundError(f"No template found matching pattern '{pattern}' in {display_name}")

    if len(files) > 1:
        file_paths = [str(f.path) for f in files]
        raise FileNotFoundError(f"Multiple templates found matching pattern '{pattern}': {file_paths}")

    file_info = files[0]
    file_info.resolve(resolver, category_dir)
    return [file_info]


async def render_content(
    session: "Session | None",
    pattern: str,
    category_dir: str,
    extra_context: Optional[TemplateContext] = None,
    category_name: Optional[str] = None,
    discover_files: Optional[Callable[[Callable[[str | Path], Path], str, str, str], Awaitable[list[FileInfo]]]] = None,
    process_context: Optional[Callable[[TemplateContext, FileInfo], Awaitable[TemplateContext]]] = None,
    prepare_partials: Optional[
        Callable[
            [FileInfo, TemplateContext | None, dict[str, object]],
            Awaitable[tuple[dict[str, str], dict[str, list[DocumentContribution]]]],
        ]
    ] = None,
    *,
    resolver: Callable[[str | Path], Path] | None = None,
) -> RenderedContent | None:
    """Render template from the category directory matching pattern.

    Args:
        session: Session to derive context from, or None to render without any
            session, project, or client context (e.g. before a project is bound).
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

    pre_partials: dict[str, str] | None = None
    pre_partial_contributions: dict[str, list[DocumentContribution]] | None = None
    try:
        if prepare_partials is not None:
            pre_partials, pre_partial_contributions = await prepare_partials(files[0], context, requirements_context)
        rendered = await render_template(
            session,
            file_info=files[0],
            base_dir=files[0].path.parent,
            project_flags=requirements_context,
            context=context,
            pre_partials=pre_partials or None,
            pre_partial_contributions=pre_partial_contributions or None,
            resolver=resolver,
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
