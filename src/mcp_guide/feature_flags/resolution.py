"""Feature flag resolution logic."""

from typing import Any, Optional

from mcp_guide.feature_flags.types import FeatureValue


def resolve_flag(
    name: str, project_flags: dict[str, FeatureValue], global_flags: dict[str, FeatureValue]
) -> Optional[FeatureValue]:
    """Resolve feature flag value using project → global → None hierarchy.

    Args:
        name: Flag name to resolve
        project_flags: Project-specific flags
        global_flags: Global flags

    Returns:
        Flag value if found, None otherwise
    """
    # Project flags take precedence
    if name in project_flags:
        return project_flags[name]

    # Fall back to global flags
    if name in global_flags:
        return global_flags[name]

    # Not found
    return None


def get_target_project(project_param: Optional[str], session: Any) -> Optional[str]:
    """Get target project name from parameter using convention.

    Args:
        project_param: Project parameter from tool call
        session: Session object for current project access

    Returns:
        Target project name, "*" for global, or None if no current project

    Raises:
        RuntimeError: If session access fails
    """
    if project_param is None:
        # None means current project
        return session.project_name  # type: ignore[no-any-return]

    # Return parameter as-is ("*" for global, specific name for specific project)
    return project_param
