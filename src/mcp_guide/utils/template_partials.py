"""Template partial utilities for path resolution and content loading."""

from pathlib import Path
from typing import Any, List

from anyio import Path as AsyncPath

from mcp_guide.core.mcp_log import get_logger

logger = get_logger(__name__)


class PartialNotFoundError(Exception):
    """Raised when a partial template file cannot be found."""

    pass


async def resolve_partial_paths(template_path: Path, includes: List[str], docroot: Path | None = None) -> List[Path]:
    """Resolve partial paths relative to template file with extension resolution.

    Args:
        template_path: Path to the template file
        includes: List of partial paths to resolve (without extensions)
        docroot: Root directory for security validation (defaults to current working directory)

    Returns:
        List of resolved absolute paths to partial files

    Raises:
        PartialNotFoundError: If partial path is outside docroot or invalid
    """
    template_dir = template_path.parent
    if docroot is None:
        docroot = Path.cwd()
    docroot = docroot.resolve()
    resolved_paths = []

    for include in includes:
        logger.trace(f"Processing include: {include}")
        # Reject absolute paths
        if include.startswith("/"):
            raise PartialNotFoundError(f"Absolute paths not allowed: {include}")

        # Resolve base path relative to the template directory
        base_path = template_dir / include
        logger.trace(f"Base path before underscore check: {base_path}")

        # Add an underscore prefix to basename if not already present
        if not base_path.name.startswith("_"):
            base_path = base_path.parent / f"_{base_path.name}"
            logger.trace(f"Added underscore prefix: {base_path}")

        # Check security first - resolve to absolute path and validate against docroot
        temp_resolved = base_path.resolve()
        logger.trace(f"Resolved absolute path: {temp_resolved}")
        try:
            temp_resolved.relative_to(docroot)
            logger.trace(f"Security check passed for: {temp_resolved}")
        except ValueError as e:
            logger.trace(f"Security check failed - path outside docroot: {include}")
            raise PartialNotFoundError(f"Partial path outside docroot: {include}") from e

        # Use common extension resolution function
        from mcp_guide.utils.file_discovery import resolve_file_with_extensions

        found_path = await resolve_file_with_extensions(base_path)

        if found_path is None:
            logger.trace(f"No partial file found for include: {include}")
            raise PartialNotFoundError(f"Partial template not found: {include} (tried all extension patterns)")

        # Resolve to an absolute path
        partial_path = found_path.resolve()
        logger.trace(f"Final resolved partial path: {partial_path}")

        resolved_paths.append(partial_path)

    logger.trace(f"All resolved partial paths: {resolved_paths}")
    return resolved_paths


async def load_partial_content(partial_path: Path, base_path: Path, context: dict[str, Any] | None = None) -> str:
    """Load content from a partial template file with frontmatter processing.

    Args:
        partial_path: Path to the partial file (may be relative)
        base_path: Base directory to resolve relative paths against
        context: Template context for frontmatter requirements checking

    Returns:
        Content of the partial file (without frontmatter if requirements met)

    Raises:
        PartialNotFoundError: If the partial file does not exist or requirements not met
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
    from mcp_guide.utils.file_discovery import resolve_file_with_extensions

    found_path = await resolve_file_with_extensions(Path(resolved_base))

    if found_path is None:
        logger.trace(f"Partial file does not exist: {resolved_base} (tried all extension patterns)")
        raise PartialNotFoundError(f"Partial template not found: {resolved_base}")

    final_path = AsyncPath(found_path)
    logger.trace(f"Resolved final partial path: {final_path}")

    try:
        content = await final_path.read_text(encoding="utf-8")

        # Process frontmatter if present
        from mcp_guide.utils.frontmatter import check_frontmatter_requirements, parse_content_with_frontmatter

        parsed = parse_content_with_frontmatter(content)

        # Check frontmatter requirements if context provided
        if parsed.frontmatter and context:
            if not check_frontmatter_requirements(parsed.frontmatter, context):
                # Requirements not met - return empty content (effectively skip partial)
                logger.debug(f"Partial {partial_path} skipped due to unmet frontmatter requirements")
                return ""

        logger.trace(f"Successfully loaded partial content ({len(parsed.content)} chars): {final_path}")
        # Return content without frontmatter
        return parsed.content

    except Exception as e:
        logger.trace(f"Failed to read partial content from {final_path}: {e}")
        raise
