"""Feature flag resolution logic."""

from typing import Optional

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.feature_flags.validators import FlagScope, get_flag_scope


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
    scope = get_flag_scope(name)

    # Feature-only flags cannot be overridden by a Project.
    if scope != FlagScope.FEATURE_ONLY and name in project_flags:
        return project_flags[name]

    # Project-only flags must be explicitly enabled on the Project.
    if scope == FlagScope.PROJECT_ONLY:
        return None

    # Fall back to global flags
    if name in global_flags:
        return global_flags[name]

    # Not found
    return None
