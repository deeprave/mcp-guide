"""Feature flag validation functions."""

from typing import List, Union

from mcp_guide.feature_flags.types import validate_feature_value_type as validate_flag_value
from mcp_guide.models import _NAME_REGEX

__all__ = ["validate_flag_name", "validate_flag_value", "validate_workflow_flag", "validate_workflow_file_flag"]


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


def validate_workflow_flag(value: Union[bool, List[str]]) -> bool:
    """Validate workflow flag value.

    Args:
        value: Workflow flag value (boolean or list of phase names)

    Returns:
        True if valid, False otherwise
    """
    if isinstance(value, bool):
        return True

    if isinstance(value, list):
        return all(isinstance(phase, str) and phase.strip() for phase in value)

    return False


def validate_workflow_file_flag(value: str) -> bool:
    """Validate workflow-file flag value.

    Args:
        value: Workflow file path

    Returns:
        True if valid, False otherwise
    """
    return isinstance(value, str) and value.strip() != ""
