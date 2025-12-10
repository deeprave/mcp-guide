"""Feature flag validation functions."""

import re
from typing import Any

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.feature_flags.types import validate_feature_value_type as validate_flag_value

__all__ = ["validate_project_name", "validate_flag_name", "validate_flag_value"]


def validate_project_name(name: str) -> bool:
    """Validate project name for feature flag contexts.

    Project names allow any UTF-8 character except control characters.
    This follows filesystem directory naming conventions.

    Args:
        name: Project name to validate

    Returns:
        True if name is valid, False otherwise
    """
    if not name:
        return False

    # Check for control characters (0x00-0x1F and 0x7F)
    return not any(ord(c) < 32 or ord(c) == 127 for c in name)


def validate_flag_name(name: str) -> bool:
    """Validate feature flag name.

    Flag names must contain only alphanumeric characters, hyphens, and underscores.
    Periods are not allowed to reserve for future dot notation access.

    Args:
        name: Flag name to validate

    Returns:
        True if name is valid, False otherwise
    """
    if not name:
        return False

    # Only alphanumeric, hyphens, and underscores
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", name))
