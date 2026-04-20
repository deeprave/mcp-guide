"""Feature flag validators and registration system."""

from collections.abc import Collection
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
from mcp_guide.feature_flags.types import FeatureValue, FeatureValueLike
from mcp_guide.feature_flags.types import validate_feature_value_type as validate_flag_value
from mcp_guide.models import _NAME_REGEX

__all__ = [
    "validate_flag_name",
    "validate_flag_value",
    "coerce_boolean_like",
    "is_value_true",
    "is_value_false",
    "make_string_choice_validator",
    "validate_boolean_or_string_flag",
    "normalise_boolean_or_string_flag",
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
_FLAG_VALIDATORS: Dict[str, Callable[[FeatureValueLike | None, bool], bool]] = {}

# Registry for flag scope restrictions
_FLAG_SCOPES: Dict[str, FlagScope] = {}

# Registry for flag-specific normalisers
_FLAG_NORMALISERS: Dict[str, Callable[[FeatureValueLike | None], FeatureValue | None]] = {}


class FlagValidationError(Exception):
    """Raised when flag validation fails."""

    pass


_TRUE_LIKE_STRINGS = frozenset({"true", "on", "enabled", "yes", "1"})
_FALSE_LIKE_STRINGS = frozenset({"false", "off", "disabled", "no", "0"})


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


def coerce_boolean_like(value: FeatureValueLike | None) -> bool | None:
    """Return canonical bool for known boolean-like inputs, else None.

    This is the single coercion rule shared across feature-flag handling.
    Callers can decide whether a non-coercible value should remain a string or
    be treated as invalid.
    """
    if value is None:
        return None
    try:
        raw = FeatureValue.from_raw(value).to_raw()
    except TypeError:
        return None

    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        lowered = raw.lower()
        if lowered in _TRUE_LIKE_STRINGS:
            return True
        if lowered in _FALSE_LIKE_STRINGS:
            return False
    return None


def is_value_true(value: FeatureValueLike | None) -> bool:
    """Check whether value is a truthy boolean-like input."""
    return coerce_boolean_like(value) is True


def is_value_false(value: FeatureValueLike | None) -> bool:
    """Check whether value is a falsy boolean-like input."""
    return coerce_boolean_like(value) is False


def make_string_choice_validator(
    choices: Collection[str],
    *,
    allow_none: bool = True,
) -> Callable[[FeatureValueLike | None, bool], bool]:
    """Build a validator for flags that accept one of a fixed set of strings.

    `None` is treated as valid by default so callers can use it for flag removal.
    """
    allowed = frozenset(choices)

    def validator(value: FeatureValueLike | None, is_project: bool) -> bool:
        del is_project
        if value is None:
            return allow_none
        try:
            raw = FeatureValue.from_raw(value).to_raw()
        except TypeError:
            return False
        return isinstance(raw, str) and raw in allowed

    return validator


validate_content_format_mime = make_string_choice_validator(["none", "plain", "mime"])
validate_template_styling = make_string_choice_validator(["plain", "headings", "full"])


def validate_allow_client_info(value: FeatureValueLike | None, is_project: bool) -> bool:
    """Validate allow-client-info flag value.

    Accepts boolean values or string representations ('enabled', 'disabled', 'on', 'off').
    Scope restriction (feature-only) is enforced by validate_flag_with_registered().

    Args:
        value: Flag value to validate
        is_project: Whether this is a project-level flag (used by scope checking)

    Returns:
        True if value is valid, False otherwise
    """
    if value is None:
        return True
    return coerce_boolean_like(value) is not None


def validate_autoupdate(value: FeatureValueLike | None, is_project: bool) -> bool:
    """Validate autoupdate flag value.

    Accepts boolean values or string representations ('enabled', 'disabled', 'on', 'off').
    Scope restriction (feature-only) is enforced by validate_flag_with_registered().

    Args:
        value: Flag value to validate
        is_project: Whether this is a project-level flag (used by scope checking)

    Returns:
        True if value is valid, False otherwise
    """
    if value is None:
        return True
    return coerce_boolean_like(value) is not None


def validate_boolean_flag(value: FeatureValueLike | None, is_project: bool) -> bool:
    """Validate simple boolean flag value.

    Accepts truthy values (True, "true", "on", "enabled") and falsy values
    (False, "false", "off", "disabled", "", None).

    Args:
        value: Flag value to validate
        is_project: True if this is a project flag, False if global

    Returns:
        True if value is valid boolean-like, False otherwise
    """
    if value is None:
        return True
    return coerce_boolean_like(value) is not None


def normalise_boolean_flag(value: FeatureValueLike | None) -> FeatureValue | None:
    """Normalise boolean-like flag values to True/False."""
    if value is None:
        return None
    coerced = coerce_boolean_like(value)
    if coerced is not None:
        return FeatureValue(coerced)
    return FeatureValue.from_raw(value)


def validate_boolean_or_string_flag(value: FeatureValueLike | None, is_project: bool) -> bool:
    """Validate the default generic feature flag shape.

    Generic flags default to either booleans or arbitrary strings. Structured
    shapes remain available only through explicit per-flag registration.
    """
    if value is None:
        return True
    try:
        raw = FeatureValue.from_raw(value).to_raw()
    except TypeError:
        return False
    return isinstance(raw, (bool, str))


def normalise_boolean_or_string_flag(value: FeatureValueLike | None) -> FeatureValue | None:
    """Normalise generic feature flags to canonical bool-or-string values."""
    if value is None:
        return None
    coerced = coerce_boolean_like(value)
    if coerced is not None:
        return FeatureValue(coerced)
    return FeatureValue.from_raw(value)


def validate_path_flag(value: FeatureValueLike | None, is_project: bool) -> bool:
    """Validate path flag value.

    Accepts non-empty, whitespace-trimmed strings (relative or absolute) without path traversal.

    Args:
        value: Flag value to validate
        is_project: True if this is a project flag, False if global

    Returns:
        True if value is a valid path string, False otherwise
    """
    if value is None:
        return False
    try:
        raw = FeatureValue.from_raw(value).to_raw()
    except TypeError:
        return False
    if not isinstance(raw, str):
        return False

    # Strip leading/trailing whitespace to avoid confusing invisible padding
    raw = raw.strip()
    if not raw:
        return False

    normalised = raw.replace("\\", "/")

    # Block path traversal
    if ".." in normalised.split("/"):
        return False

    # Block system directories for absolute paths
    if normalised.startswith("/"):
        from mcp_guide.filesystem.system_directories import is_system_directory

        if is_system_directory(normalised):
            return False

    return True


def normalise_path_flag(value: FeatureValueLike | None) -> FeatureValue | None:
    """Normalise path flag value by using POSIX separators and ensuring trailing slash."""
    if value is None:
        return None
    wrapped = FeatureValue.from_raw(value)
    raw = wrapped.to_raw()
    if isinstance(raw, str):
        normalised = raw.replace("\\", "/")
        if not normalised.endswith("/"):
            normalised += "/"
        return FeatureValue(normalised)
    return wrapped


def normalise_flag(flag_name: str, value: FeatureValueLike | None) -> FeatureValue | None:
    """Normalise flag value using its registered normaliser.

    Args:
        flag_name: Name of the flag
        value: Flag value to normalise

    Returns:
        Normalised flag value, or original if no normaliser registered
    """
    if value is None:
        return None
    wrapped_value = FeatureValue.from_raw(value)
    normaliser = _FLAG_NORMALISERS.get(flag_name, normalise_boolean_or_string_flag)
    return normaliser(wrapped_value)


def register_flag_validator(
    flag_name: str,
    validator: Callable[[FeatureValueLike | None, bool], bool],
    scope: FlagScope = FlagScope.BOTH,
    normaliser: Callable[[FeatureValueLike | None], FeatureValue | None] | None = None,
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


def validate_flag_with_registered(flag_name: str, value: FeatureValueLike | None, is_project: bool) -> None:
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
    validator = _FLAG_VALIDATORS.get(flag_name, validate_boolean_or_string_flag)
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
register_flag_validator(
    FLAG_ALLOW_CLIENT_INFO,
    validate_allow_client_info,
    FlagScope.FEATURE_ONLY,
    normaliser=normalise_boolean_flag,
)
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

# Import built-in workflow flag registrations after the core registry is defined.
from mcp_guide.workflow import flags as _workflow_flags  # noqa: F401
