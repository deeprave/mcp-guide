"""Feature flag validators and registration system."""

from typing import Callable, Dict

from mcp_guide.feature_flags.constants import (
    FLAG_ALLOW_CLIENT_INFO,
    FLAG_CONTENT_FORMAT_MIME,
    FLAG_CONTENT_STYLE,
)
from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.feature_flags.types import validate_feature_value_type as validate_flag_value
from mcp_guide.models import _NAME_REGEX

__all__ = [
    "validate_flag_name",
    "validate_flag_value",
    "register_flag_validator",
    "validate_flag_with_registered",
    "clear_validators",
    "FlagValidationError",
]

# Registry for flag-specific validators
_FLAG_VALIDATORS: Dict[str, Callable[[FeatureValue, bool], bool]] = {}


class FlagValidationError(Exception):
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


def validate_content_format_mime(value: FeatureValue, is_project: bool) -> bool:
    """Validate content-format-mime flag value.

    Args:
        value: Flag value to validate
        is_project: True if this is a project flag, False if global

    Returns:
        True if value is valid, False otherwise
    """
    return value in [None, "none", "plain", "mime"]


def validate_template_styling(value: FeatureValue, is_project: bool) -> bool:
    """Validate content-style flag value.

    Args:
        value: Flag value to validate
        is_project: True if this is a project flag, False if global

    Returns:
        True if value is valid, False otherwise
    """
    return value in [None, "plain", "headings", "full"]


def validate_allow_client_info(value: FeatureValue, is_project: bool) -> bool:
    """Validate allow-client-info flag value.

    This flag is global-only and cannot be set at project level.

    Args:
        value: Flag value to validate
        is_project: True if this is a project flag, False if global

    Returns:
        True if value is valid, False otherwise
    """
    # Reject project-level setting
    if is_project:
        return False

    # Accept enable values (will be normalized to True)
    if value is True or value in ["true", "enabled", "on"]:
        return True

    # Accept disable values (will be normalized to None)
    if value is False or value is None or value in ["false", "disabled", "off"]:
        return True

    return False


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
        FlagValidationError: If validation fails
    """
    # None values are used for deletion and should skip validation
    if value is None:
        return

    validator = _FLAG_VALIDATORS.get(flag_name)
    if validator and not validator(value, is_project):
        flag_type = "project" if is_project else "global"
        raise FlagValidationError(f"Invalid {flag_type} flag '{flag_name}' value: {value}")


def clear_validators() -> None:
    """Clear all registered validators. For testing only."""
    _FLAG_VALIDATORS.clear()


# Register validators
register_flag_validator(FLAG_CONTENT_FORMAT_MIME, validate_content_format_mime)
register_flag_validator(FLAG_CONTENT_STYLE, validate_template_styling)
register_flag_validator(FLAG_ALLOW_CLIENT_INFO, validate_allow_client_info)
