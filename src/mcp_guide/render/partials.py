"""Template partial utilities for path resolution and content loading."""

import re
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from anyio import Path as AsyncPath

from mcp_guide.content_limits import DEFAULT_MAX_CONTENT_LIMIT, ensure_within_limit
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.lazy_path import LazyPath

if TYPE_CHECKING:
    from mcp_guide.render.frontmatter import Frontmatter

logger = get_logger(__name__)


class PartialNotFoundError(Exception):
    """Raised when a partial template file cannot be found."""

    pass


class UnsafePartialPathError(ValueError):
    """Raised when a partial reference is not a permitted server path."""

    pass


_ENVIRONMENT_VARIABLE_REFERENCE = re.compile(r"\$(?:[A-Za-z_][A-Za-z0-9_]*|\{[^}]+\})")


def _reject_unsafe_reference(partial_path: Path) -> None:
    """Reject path expansion syntax which has no meaning in template references."""
    path_text = str(partial_path)
    if path_text.startswith("~"):
        raise UnsafePartialPathError("home-anchored partial references are not permitted")
    if _ENVIRONMENT_VARIABLE_REFERENCE.search(path_text):
        raise UnsafePartialPathError("environment-variable partial references are not permitted")


async def load_partial_content(
    partial_path: Path,
    base_path: Path,
    context: dict[str, Any] | None = None,
    *,
    resolver: Callable[[str | Path], Path] | None = None,
    max_content_limit: int = DEFAULT_MAX_CONTENT_LIMIT,
) -> tuple[str, "Frontmatter"]:
    """Load content from a partial template file with frontmatter processing.

    Args:
        partial_path: Path to the partial file (may be relative)
        base_path: Including template directory for relative partial references
        context: Template context for frontmatter requirements checking
        resolver: Server-side document-root resolver required for filesystem reads

    Returns:
        Tuple of (content, frontmatter) where:
        - content: Content of the partial file (without frontmatter if requirements met, empty if not met)
        - frontmatter: Frontmatter dictionary (may be empty if no frontmatter)

    Raises:
        PartialNotFoundError: If the partial file does not exist
    """
    _reject_unsafe_reference(partial_path)
    if resolver is None:
        raise UnsafePartialPathError("filesystem partial loading requires a document-root resolver")

    # Convert to AsyncPath immediately
    base_async = AsyncPath(base_path)

    logger.trace(f"Loading partial: partial_path={partial_path}, base_path={base_async}")

    # Resolve relative references from the template that includes the partial.
    resolved_base = Path(partial_path) if LazyPath(partial_path).is_absolute() else Path(base_async / partial_path)

    logger.trace(f"Base partial path: {resolved_base}")

    found_path = await _resolve_contained_file_with_extensions(resolved_base, resolver)

    if found_path is None:
        logger.trace(f"Partial file does not exist: {resolved_base} (tried all extension patterns)")
        raise PartialNotFoundError(f"Partial template not found: {resolved_base}")

    final_path = AsyncPath(found_path)
    logger.trace(f"Resolved final partial path: {final_path}")

    try:
        # Partials are static Guide documents.  A size preflight is sufficient because
        # they are not expected to change while a request is being rendered.
        stat = await final_path.stat()
        ensure_within_limit(stat.st_size, limit_name="max-content-limit", limit=max_content_limit)
        content = await final_path.read_text(encoding="utf-8")

        # Process frontmatter: parse, check requirements, render instruction/description
        from mcp_guide.render.context import TemplateContext
        from mcp_guide.render.frontmatter import process_frontmatter

        render_context = TemplateContext(context) if context else None
        processed = await process_frontmatter(content, context, render_context)

        if processed is None:
            # Requirements not met - return empty content with empty frontmatter
            logger.debug(f"Partial {partial_path} skipped due to unmet frontmatter requirements")
            from mcp_guide.render.frontmatter import parse_content_with_frontmatter

            parsed = parse_content_with_frontmatter(content)
            return ("", parsed.frontmatter)

        logger.trace(f"Successfully loaded partial content ({len(processed.content)} chars): {final_path}")
        # Return content and frontmatter
        return (processed.content, processed.frontmatter)

    except Exception as e:
        logger.trace(f"Failed to read partial content from {final_path}: {e}")
        raise


async def _resolve_contained_file_with_extensions(
    base_path: Path,
    resolver: Callable[[str | Path], Path],
) -> Path | None:
    """Find an existing extension candidate without probing outside docroot."""
    from mcp_guide.discovery.files import TEMPLATE_EXTENSIONS

    candidates = [
        base_path,
        base_path.with_suffix(".md"),
        *(base_path.with_suffix(extension) for extension in TEMPLATE_EXTENSIONS),
        *(base_path.with_suffix(f".md{extension}") for extension in TEMPLATE_EXTENSIONS),
    ]
    document_root = resolver(".").resolve()

    for candidate in candidates:
        try:
            contained_path = resolver(candidate)
            canonical_path = contained_path.resolve()
            canonical_path.relative_to(document_root)
        except ValueError as error:
            raise UnsafePartialPathError("partial reference must remain within the document root") from error

        if await AsyncPath(canonical_path).exists():
            return canonical_path

    return None
