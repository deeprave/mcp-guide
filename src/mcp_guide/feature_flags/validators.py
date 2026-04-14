"""Feature flag validators and registration system."""

from enum import Enum
from typing import Callable, Dict

from mcp_guide.feature_flags.constants import (
    FLAG_ALLOW_CLIENT_INFO,
    FLAG_AUTOUPDATE,
    FLAG_COMMAND,
    FLAG_CONTENT_FORMAT,
    FLAG_CONTENT_STYLE,
    FLAG_GUIDE_DEVELOPMENT,
    FLAG_ONBOARDED,
    FLAG_PATH_DOCUMENTS,
    FLAG_PATH_EXPORT,
    FLAG_RESOURCE,
)
from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.feature_flags.types import validate_feature_value_type as validate_flag_value
from mcp_guide.models import _NAME_REGEX

__all__ = [
    "validate_flag_name",
    "validate_flag_value",
    "register_flag_validator",
    "validate_flag_with_registered",
    "normalise_flag",
    "clear_validators",
    "FlagValidationError",
    "FlagScope",
]


class FlagScope(Enum):
    """Flag scope restrictions.

    Defines where a flag can be set:
    - FEATURE_ONLY: Can only be set at feature/global level
    - PROJECT_ONLY: Can only be set at project level
    - BOTH: Can be set at either level (default)
    """

    FEATURE_ONLY = "feature"
    PROJECT_ONLY = "project"
    BOTH = "both"


# Registry for flag-specific validators
_FLAG_VALIDATORS: Dict[str, Callable[[FeatureValue, bool], bool]] = {}

# Registry for flag scope restrictions
_FLAG_SCOPES: Dict[str, FlagScope] = {}

# Registry for flag-specific normalisers
_FLAG_NORMALISERS: Dict[str, Callable[[FeatureValue], FeatureValue]] = {}


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
    """Validate content-format flag value.

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

    Accepts boolean values or string representations ('enabled', 'disabled', 'on', 'off').
    Scope restriction (feature-only) is enforced by validate_flag_with_registered().

    Args:
        value: Flag value to validate
        is_project: Whether this is a project-level flag (used by scope checking)

    Returns:
        True if value is valid, False otherwise
    """
    # Accept enable values (will be normalized to True)
    if value is True or value in ["true", "enabled", "on"]:
        return True

    # Accept disable values (will be normalized to None)
    if value is False or value is None or value in ["false", "disabled", "off"]:
        return True

    return False


def validate_autoupdate(value: FeatureValue, is_project: bool) -> bool:
    """Validate autoupdate flag value.

    Accepts boolean values or string representations ('enabled', 'disabled', 'on', 'off').
    Scope restriction (feature-only) is enforced by validate_flag_with_registered().

    Args:
        value: Flag value to validate
        is_project: Whether this is a project-level flag (used by scope checking)

    Returns:
        True if value is valid, False otherwise
    """
    # Accept boolean values only
    if value is True or value in ["true", "enabled", "on"]:
        return True

    if value is False or value is None or value in ["false", "disabled", "off"]:
        return True

    return False


def validate_boolean_flag(value: FeatureValue, is_project: bool) -> bool:
    """Validate simple boolean flag value.

    Accepts truthy values (True, "true", "on", "enabled") and falsy values
    (False, "false", "off", "disabled", "", None).

    Args:
        value: Flag value to validate
        is_project: True if this is a project flag, False if global

    Returns:
        True if value is valid boolean-like, False otherwise
    """
    # Accept boolean types
    if isinstance(value, bool):
        return True

    # Accept None (used for deletion/disable)
    if value is None:
        return True

    # Accept string boolean representations
    if isinstance(value, str):
        return value.lower() in ["true", "false", "on", "off", "enabled", "disabled", ""]

    return False


def normalise_boolean_flag(value: FeatureValue) -> FeatureValue:
    """Normalise boolean-like flag values to True/False."""
    if isinstance(value, bool) or value is None:
        return value

    if isinstance(value, str):
        lowered = value.lower()
        if lowered in ["true", "on", "enabled"]:
            return True
        if lowered in ["false", "off", "disabled", ""]:
            return False

    return value


def validate_path_flag(value: FeatureValue, is_project: bool) -> bool:
    """Validate path flag value.

    Accepts non-empty, whitespace-trimmed strings (relative or absolute) without path traversal.

    Args:
        value: Flag value to validate
        is_project: True if this is a project flag, False if global

    Returns:
        True if value is a valid path string, False otherwise
    """
    if not isinstance(value, str):
        return False

    # Strip leading/trailing whitespace to avoid confusing invisible padding
    value = value.strip()
    if not value:
        return False

    normalised = value.replace("\\", "/")

    # Block path traversal
    if ".." in normalised.split("/"):
        return False

    # Block system directories for absolute paths
    if normalised.startswith("/"):
        from mcp_guide.filesystem.system_directories import is_system_directory

        if is_system_directory(normalised):
            return False

    return True


def normalise_path_flag(value: FeatureValue) -> FeatureValue:
    """Normalise path flag value by using POSIX separators and ensuring trailing slash."""
    if isinstance(value, str):
        normalised = value.replace("\\", "/")
        if not normalised.endswith("/"):
            normalised += "/"
        return normalised
    return value


def normalise_flag(flag_name: str, value: FeatureValue) -> FeatureValue:
    """Normalise flag value using its registered normaliser.

    Args:
        flag_name: Name of the flag
        value: Flag value to normalise

    Returns:
        Normalised flag value, or original if no normaliser registered
    """
    normaliser = _FLAG_NORMALISERS.get(flag_name)
    if normaliser:
        return normaliser(value)
    return value


def register_flag_validator(
    flag_name: str,
    validator: Callable[[FeatureValue, bool], bool],
    scope: FlagScope = FlagScope.BOTH,
    normaliser: Callable[[FeatureValue], FeatureValue] | None = None,
) -> None:
    """Register a validator function for a specific flag.

    Args:
        flag_name: Name of the flag
        validator: Function that validates the flag value and context
        scope: Scope restriction for the flag (default: BOTH)
        normaliser: Optional function to normalise the value before validation
    """
    _FLAG_VALIDATORS[flag_name] = validator
    _FLAG_SCOPES[flag_name] = scope
    if normaliser:
        _FLAG_NORMALISERS[flag_name] = normaliser


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

    # Check scope restrictions first
    scope = _FLAG_SCOPES.get(flag_name)
    if scope:
        if scope == FlagScope.FEATURE_ONLY and is_project:
            raise FlagValidationError(f"Cannot set project flag `{flag_name}`, must be a feature flag")
        if scope == FlagScope.PROJECT_ONLY and not is_project:
            raise FlagValidationError(f"Cannot set feature flag `{flag_name}`, must be a project flag")

    # Validate value
    validator = _FLAG_VALIDATORS.get(flag_name)
    if validator and not validator(value, is_project):
        flag_type = "project" if is_project else "feature"
        raise FlagValidationError(f"Invalid {flag_type} flag `{flag_name}` value: {value}")


def clear_validators() -> None:
    """Clear all registered validators. For testing only."""
    _FLAG_VALIDATORS.clear()
    _FLAG_SCOPES.clear()
    _FLAG_NORMALISERS.clear()


# Register validators
register_flag_validator(FLAG_CONTENT_FORMAT, validate_content_format_mime)
register_flag_validator(FLAG_CONTENT_STYLE, validate_template_styling)
register_flag_validator(FLAG_ALLOW_CLIENT_INFO, validate_allow_client_info, FlagScope.FEATURE_ONLY)
register_flag_validator(
    FLAG_AUTOUPDATE,
    validate_autoupdate,
    FlagScope.FEATURE_ONLY,
    normaliser=normalise_boolean_flag,
)
register_flag_validator(FLAG_GUIDE_DEVELOPMENT, validate_boolean_flag, normaliser=normalise_boolean_flag)
register_flag_validator(FLAG_RESOURCE, validate_boolean_flag, normaliser=normalise_boolean_flag)
register_flag_validator(FLAG_COMMAND, validate_boolean_flag, normaliser=normalise_boolean_flag)
register_flag_validator(FLAG_PATH_DOCUMENTS, validate_path_flag, normaliser=normalise_path_flag)
register_flag_validator(FLAG_PATH_EXPORT, validate_path_flag, normaliser=normalise_path_flag)
register_flag_validator(
    FLAG_ONBOARDED, validate_boolean_flag, scope=FlagScope.PROJECT_ONLY, normaliser=normalise_boolean_flag
)
