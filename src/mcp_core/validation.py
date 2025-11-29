"""Validation functions for tool arguments."""

from pathlib import Path
from typing import Optional

# Error messages
ERR_ABSOLUTE_PATH = "Absolute paths are not allowed"
ERR_PATH_TRAVERSAL = "Path traversal is not allowed"
ERR_INVALID_PATH_COMPONENT = "Invalid path component: {}"
ERR_INVALID_PATTERN_COMPONENT = "Invalid pattern component: {}"
ERR_DESCRIPTION_TOO_LONG = "Description exceeds {} characters"
ERR_INVALID_CHARACTERS = "Description contains quote characters"

# Default instruction for validation errors
DEFAULT_INSTRUCTION = "Return error to user without attempting remediation"


class ValidationError(ValueError):
    """Validation error with structured information for agents.

    Args:
        message: Human-readable error message for the user
        error_type: Machine-readable error classification (default: "validation_error")
        instruction: Instruction to the agent on how to handle this error
    """

    def __init__(
        self,
        message: str,
        error_type: Optional[str] = None,
        instruction: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type or "validation_error"
        self.instruction = instruction or DEFAULT_INSTRUCTION


def is_absolute_path(path: str) -> bool:
    """Check if path is absolute (Unix, Windows, or UNC).

    Args:
        path: Path to check

    Returns:
        True if path is absolute
    """
    if not path:
        return False

    # Unix absolute path
    if path.startswith("/"):
        return True

    # Windows drive letter (C:, D:, etc.)
    if len(path) > 1 and path[1] == ":":
        return True

    # UNC path (\\server\share)
    return True if path.startswith("\\\\") else Path(path).is_absolute()


def validate_directory_path(path: Optional[str], default: str) -> str:
    """Validate directory path for safety.

    Args:
        path: Directory path to validate (or None/empty for default)
        default: Default value if path is None/empty

    Returns:
        Validated path

    Raises:
        ValidationError: If path is invalid
    """
    if not path:
        return default

    if is_absolute_path(path):
        raise ValidationError(ERR_ABSOLUTE_PATH, error_type="absolute_path")

    # Normalize path separators and check individual components for traversal attempts
    # This avoids rejecting benign names like "file..txt" while still blocking "../" usage
    normalized_path = path.replace("\\", "/")
    parts = normalized_path.split("/")
    if any(part == ".." for part in parts):
        raise ValidationError(ERR_PATH_TRAVERSAL, error_type="traversal_attempt")

    parts = path.replace("\\", "/").split("/")
    for part in parts:
        if part.startswith("__") or part.endswith("__"):
            raise ValidationError(
                ERR_INVALID_PATH_COMPONENT.format(part),
                error_type="invalid_component",
            )

    return path


def validate_description(desc: Optional[str], max_length: int = 500) -> Optional[str]:
    """Validate description for length and content.

    Args:
        desc: Description to validate (or None/empty)
        max_length: Maximum allowed length (default: 500)

    Returns:
        Validated description

    Raises:
        ValidationError: If description is invalid
    """
    if desc is None or desc == "":
        return desc

    if len(desc) > max_length:
        raise ValidationError(
            ERR_DESCRIPTION_TOO_LONG.format(max_length),
            error_type="description_too_long",
        )

    if '"' in desc or "'" in desc:
        raise ValidationError(ERR_INVALID_CHARACTERS, error_type="invalid_characters")

    return desc


def validate_pattern(pattern: str) -> str:
    """Validate glob pattern for safety.

    Args:
        pattern: Glob pattern to validate

    Returns:
        Validated pattern

    Raises:
        ValidationError: If pattern is invalid
    """
    if is_absolute_path(pattern):
        raise ValidationError(ERR_ABSOLUTE_PATH, error_type="absolute_path")

    if ".." in pattern:
        raise ValidationError(ERR_PATH_TRAVERSAL, error_type="traversal_attempt")

    parts = pattern.replace("\\", "/").split("/")
    for part in parts:
        if part.startswith("__") or part.endswith("__"):
            raise ValidationError(
                ERR_INVALID_PATTERN_COMPONENT.format(part),
                error_type="invalid_pattern",
            )

    return pattern
