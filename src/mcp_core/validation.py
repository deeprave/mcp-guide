"""Validation functions for tool arguments."""

from pathlib import Path
from typing import Any, Optional

from mcp_core.result import Result

# Error messages
ERR_ABSOLUTE_PATH = "Absolute paths are not allowed"
ERR_PATH_TRAVERSAL = "Path traversal is not allowed"
ERR_INVALID_PATH_COMPONENT = "Invalid path component: {}"
ERR_INVALID_PATTERN_COMPONENT = "Invalid pattern component: {}"
ERR_DESCRIPTION_TOO_LONG = "Description exceeds {} characters"
ERR_INVALID_CHARACTERS = "Description contains quote characters"

# Default instruction for validation errors
DEFAULT_INSTRUCTION = "Return error to user without attempting remediation"


class ArgValidationError(ValueError):
    """Argument validation error that collects multiple validation failures.

    Args:
        errors: List of validation errors with field and message
        message: Optional summary message (auto-generated if not provided)
        instruction: Optional instruction to the agent on how to handle this error
    """

    def __init__(
        self,
        errors: list[dict[str, str]],
        message: Optional[str] = None,
        instruction: Optional[str] = None,
    ):
        self.errors = errors
        self.message = message or self._generate_message()
        self.instruction = instruction or DEFAULT_INSTRUCTION
        super().__init__(self.message)

    def _generate_message(self) -> str:
        """Generate summary message from errors."""
        count = len(self.errors)
        if count == 1:
            return f"Validation error: {self.errors[0]['message']}"
        return f"{count} validation errors occurred"

    def to_result(
        self,
        message: Optional[str] = None,
        instruction: Optional[str] = None,
    ) -> Result[Any]:
        """Convert to Result with structured error data.

        Args:
            message: Override summary message
            instruction: Override agent instruction

        Returns:
            Result with validation errors in error_data
        """
        result: Result[Any] = Result.failure(
            error=message or self.message,
            error_type="validation_error",
        )
        result.error_data = {"validation_errors": self.errors}
        result.instruction = instruction or self.instruction
        return result


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
        ArgValidationError: If path is invalid
    """
    if not path:
        return default

    if is_absolute_path(path):
        raise ArgValidationError([{"field": "path", "message": ERR_ABSOLUTE_PATH}])

    # Normalize path separators and check individual components for traversal attempts
    # This avoids rejecting benign names like "file..txt" while still blocking "../" usage
    normalized_path = path.replace("\\", "/")
    parts = normalized_path.split("/")
    if any(part == ".." for part in parts):
        raise ArgValidationError([{"field": "path", "message": ERR_PATH_TRAVERSAL}])

    parts = path.replace("\\", "/").split("/")
    for part in parts:
        if part.startswith("__") or part.endswith("__"):
            raise ArgValidationError([{"field": "path", "message": ERR_INVALID_PATH_COMPONENT.format(part)}])

    return path


def validate_description(desc: Optional[str], max_length: int = 500) -> Optional[str]:
    """Validate description for length and content.

    Args:
        desc: Description to validate (or None/empty)
        max_length: Maximum allowed length (default: 500)

    Returns:
        Validated description

    Raises:
        ArgValidationError: If description is invalid
    """
    if desc is None or desc == "":
        return desc

    if len(desc) > max_length:
        raise ArgValidationError([{"field": "description", "message": ERR_DESCRIPTION_TOO_LONG.format(max_length)}])

    if '"' in desc or "'" in desc:
        raise ArgValidationError([{"field": "description", "message": ERR_INVALID_CHARACTERS}])

    return desc


def validate_pattern(pattern: str) -> str:
    """Validate glob pattern for safety.

    Args:
        pattern: Glob pattern to validate

    Returns:
        Validated pattern

    Raises:
        ArgValidationError: If pattern is invalid
    """
    if is_absolute_path(pattern):
        raise ArgValidationError([{"field": "pattern", "message": ERR_ABSOLUTE_PATH}])

    if ".." in pattern:
        raise ArgValidationError([{"field": "pattern", "message": ERR_PATH_TRAVERSAL}])

    parts = pattern.replace("\\", "/").split("/")
    for part in parts:
        if part.startswith("__") or part.endswith("__"):
            raise ArgValidationError([{"field": "pattern", "message": ERR_INVALID_PATTERN_COMPONENT.format(part)}])

    return pattern
