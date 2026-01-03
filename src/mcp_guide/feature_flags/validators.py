"""Feature flag validators and registration system."""

from typing import Callable, Dict

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.feature_flags.types import validate_feature_value_type as validate_flag_value
from mcp_guide.models import _NAME_REGEX

__all__ = [
    "validate_flag_name",
    "validate_flag_value",
    "register_flag_validator",
    "validate_flag_with_registered",
    "clear_validators",
]

# Registry for flag-specific validators
_FLAG_VALIDATORS: Dict[str, Callable[[FeatureValue, bool], bool]] = {}


class ValidationError(Exception):
    """Raised when flag validation fails."""

    pass


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


def register_flag_validator(flag_name: str, validator: Callable[[FeatureValue, bool], bool]) -> None:
    """Register a validator function for a specific flag.

    Args:
        flag_name: Name of the flag
        validator: Function that validates the flag value and context
    """
    _FLAG_VALIDATORS[flag_name] = validator


def validate_flag_with_registered(flag_name: str, value: FeatureValue, is_project: bool) -> None:
    """Validate a flag value using its registered validator.

    Args:
        flag_name: Name of the flag
        value: Flag value to validate
        is_project: True if this is a project flag, False if global

    Raises:
        ValidationError: If validation fails
    """
    validator = _FLAG_VALIDATORS.get(flag_name)
    if validator and not validator(value, is_project):
        flag_type = "project" if is_project else "global"
        raise ValidationError(f"Invalid {flag_type} flag '{flag_name}' value: {value}")


def clear_validators() -> None:
    """Clear all registered validators. For testing only."""
    _FLAG_VALIDATORS.clear()
