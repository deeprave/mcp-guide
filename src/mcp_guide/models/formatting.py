"""Formatting utilities for project data."""

from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.feature_flags.types import to_raw_feature_value

if TYPE_CHECKING:
    from mcp_guide.models.project import Project
    from mcp_guide.session import Session

logger = get_logger(__name__)


def _normalise_effective_flags(session: "Session | None", flags: dict[str, Any]) -> dict[str, Any]:
    """Apply session-bound normalisation after ordinary flag resolution."""
    from mcp_guide.feature_flags.constants import FLAG_WORKFLOW
    from mcp_guide.feature_flags.types import FeatureValue, to_raw_feature_value
    from mcp_guide.workflow.flags import parse_workflow_phases

    # A linked checkout must be able to receive its local workflow file, even
    # when the root agent has disabled workflow for the project. This is an
    # effective value only; it never changes persisted flags.
    if session is not None and session.is_worktree():
        workflow_value = flags.get(FLAG_WORKFLOW)
        workflow_raw = to_raw_feature_value(workflow_value) if workflow_value is not None else False
        workflow_enabled = (
            parse_workflow_phases(workflow_raw).enabled if isinstance(workflow_raw, bool | list) else False
        )
        if not workflow_enabled:
            return {**flags, FLAG_WORKFLOW: FeatureValue(["discussion", "implementation"])}
    return flags


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
        session: When supplied, include the project's stored flags (optional)

    Returns:
        Formatted project data dictionary
    """
    collections, categories = _format_categories_and_collections(project, verbose)
    result: dict[str, Any] = {"collections": collections, "categories": categories}

    # Project listings expose only stored flags for the formatted Project.
    if session is not None:
        flags = project.project_flags
        result["flags"] = (
            {name: to_raw_feature_value(value) for name, value in flags.items()} if verbose else list(flags.keys())
        )
    return result


async def resolve_all_flags(session: "Session | None") -> dict[str, Any]:
    """Resolve all flags by merging project and global flags.

    With no session (no project bound), global flags still resolve; only
    project-flag overrides are unavailable.

    Returns:
        Resolved flags dictionary, or empty dict if resolution fails
    """
    from mcp_guide.feature_flags.constants import FLAG_HANDOFF_CONTEXT
    from mcp_guide.feature_flags.resolution import resolve_flag

    try:
        # Get all flags
        project_flags = await session.project_flags().list() if session is not None else {}
        from mcp_guide.runtime import get_runtime

        runtime = get_runtime()
        global_flags = await runtime.feature_flags().list()

        # Get all unique flag names
        all_flag_names = set(project_flags.keys()) | set(global_flags.keys())

        # Resolve each flag
        resolved = {}
        for name in all_flag_names:
            value = resolve_flag(name, project_flags, global_flags)
            if value is not None:
                resolved[name] = value

        # Handoff context is intentionally enabled unless explicitly false.
        # Surface that default to ordinary template conditionals as well as
        # frontmatter requirement evaluation.
        resolved.setdefault(FLAG_HANDOFF_CONTEXT, True)

        return _normalise_effective_flags(session, resolved)
    except Exception as e:
        # Log unexpected errors for debugging, but continue with empty flags
        # since flags are supplementary data
        logger.debug(f"Flag resolution failed: {e}")
        return {}
