"""Feature flag resolution logic."""

from typing import Optional

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
