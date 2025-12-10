"""Feature flag validation functions."""

from mcp_guide.feature_flags.types import validate_feature_value_type as validate_flag_value
from mcp_guide.models import _NAME_REGEX

__all__ = ["validate_flag_name", "validate_flag_value"]


def validate_flag_name(name: str) -> bool:
    """Validate feature flag name.

    Flag names must contain only Unicode alphanumeric characters, hyphens, and underscores.
    Periods are not allowed to reserve for future dot notation access.

    Args:
        name: Flag name to validate

    Returns:
        True if name is valid, False otherwise
    """
    if not name:
        return False

    # Use same Unicode-aware validation as project names
    return bool(_NAME_REGEX.match(name))
