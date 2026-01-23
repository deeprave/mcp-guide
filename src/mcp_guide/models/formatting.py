"""Formatting utilities for project data."""

from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.core.mcp_log import get_logger

if TYPE_CHECKING:
    from mcp_guide.models.project import Project
    from mcp_guide.session import Session

logger = get_logger(__name__)


def _format_categories_and_collections(project: "Project", verbose: bool) -> tuple[Any, Any]:
    """Format categories and collections for tool responses.

    Args:
        project: Project to format
        verbose: If True, include full details; if False, names only

    Returns:
        Tuple of (collections, categories) formatted data
    """
    from typing import Union

    collections: Union[list[dict[str, Any]], list[str]]
    categories: Union[list[dict[str, Any]], list[str]]

    if verbose:
        collections = [
            {"name": name, "description": c.description, "categories": c.categories}
            for name, c in project.collections.items()
        ]
        categories = [
            {"name": name, "dir": c.dir, "patterns": list(c.patterns), "description": c.description}
            for name, c in project.categories.items()
        ]
    else:
        collections = list(project.collections.keys())
        categories = list(project.categories.keys())

    return collections, categories


async def format_project_data(
    project: "Project", verbose: bool = False, session: Optional["Session"] = None
) -> dict[str, Any]:
    """Format project data for tool responses.

    Args:
        project: Project to format
        verbose: If True, include full details; if False, names only
        session: Session for flag resolution (optional)

    Returns:
        Formatted project data dictionary
    """
    collections, categories = _format_categories_and_collections(project, verbose)
    result: dict[str, Any] = {"collections": collections, "categories": categories}

    # Add applied profiles if any
    applied_profiles = project.metadata.get("applied_profiles", [])
    if applied_profiles:
        result["applied_profiles"] = applied_profiles

    # Add resolved flags if session is available
    if session is not None:
        flags = await resolve_all_flags(session)
        result["flags"] = flags if verbose else list(flags.keys())
    return result


async def resolve_all_flags(session: "Session") -> dict[str, Any]:
    """Resolve all flags by merging project and global flags.

    Returns:
        Resolved flags dictionary, or empty dict if resolution fails
    """
    from mcp_guide.feature_flags.resolution import resolve_flag

    try:
        # Get all flags
        project_flags = await session.project_flags().list()
        global_flags = await session.feature_flags().list()

        # Get all unique flag names
        all_flag_names = set(project_flags.keys()) | set(global_flags.keys())

        # Resolve each flag
        resolved = {}
        for name in all_flag_names:
            value = resolve_flag(name, project_flags, global_flags)
            if value is not None:
                resolved[name] = value

        return resolved
    except Exception as e:
        # Log unexpected errors for debugging, but continue with empty flags
        # since flags are supplementary data
        logger.debug(f"Flag resolution failed: {e}")
        return {}
