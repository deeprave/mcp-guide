"""Template partial utilities for path resolution and content loading."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from anyio import Path as AsyncPath

from mcp_guide.core.mcp_log import get_logger

if TYPE_CHECKING:
    from mcp_guide.render.frontmatter import Frontmatter

logger = get_logger(__name__)


class PartialNotFoundError(Exception):
    """Raised when a partial template file cannot be found."""

    pass


async def load_partial_content(
    partial_path: Path, base_path: Path, context: dict[str, Any] | None = None
) -> tuple[str, "Frontmatter"]:
    """Load content from a partial template file with frontmatter processing.

    Args:
        partial_path: Path to the partial file (may be relative)
        base_path: Base directory to resolve relative paths against
        context: Template context for frontmatter requirements checking

    Returns:
        Tuple of (content, frontmatter) where:
        - content: Content of the partial file (without frontmatter if requirements met, empty if not met)
        - frontmatter: Frontmatter dictionary (may be empty if no frontmatter)

    Raises:
        PartialNotFoundError: If the partial file does not exist
    """
    # Convert to AsyncPath immediately
    partial_async = AsyncPath(partial_path)
    base_async = AsyncPath(base_path)

    logger.trace(f"Loading partial: partial_path={partial_async}, base_path={base_async}")

    # Resolve the final path
    if partial_async.is_absolute():
        resolved_base = partial_async
    else:
        resolved_base = base_async / partial_path

    logger.trace(f"Base partial path: {resolved_base}")

    # Use common extension resolution function
    from mcp_guide.discovery.files import resolve_file_with_extensions

    found_path = await resolve_file_with_extensions(Path(resolved_base))

    if found_path is None:
        logger.trace(f"Partial file does not exist: {resolved_base} (tried all extension patterns)")
        raise PartialNotFoundError(f"Partial template not found: {resolved_base}")

    final_path = AsyncPath(found_path)
    logger.trace(f"Resolved final partial path: {final_path}")

    try:
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
