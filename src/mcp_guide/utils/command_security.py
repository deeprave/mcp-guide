"""Security validation utilities for command execution.

Note: All validation functions use pure path operations (PurePath) without filesystem I/O,
making them inherently fast and suitable for both sync and async contexts.
"""

import re
from pathlib import PurePath
from typing import List, Optional


def _validate_common_security(path: str) -> Optional[str]:
    """Common validation logic shared across validation functions."""
    if not path:
        return "Command name cannot be empty"
    return None


def _validate_control_chars(path: str) -> Optional[str]:
    """Validate control characters (for raw validation)."""
    if "\x00" in path or "\n" in path or "\r" in path or "\t" in path:
        return "Command contains invalid characters"
    return None


def _validate_dangerous_chars(path: str) -> Optional[str]:
    """Validate dangerous shell characters (for raw validation)."""
    dangerous_chars = [";", "|", "`", "$", "(", ")", "&", "<", ">"]
    if any(char in path for char in dangerous_chars):
        return "Command contains potentially dangerous characters"
    return None


def validate_command_path(command_path: str) -> Optional[str]:
    """Validate command path for security.

    Args:
        command_path: Command path to validate (e.g., "help", "create/category")

    Returns:
        None if valid, error message if invalid
    """
    if error := _validate_common_security(command_path):
        return error

    # Early length check before any path operations
    if len(command_path) > 100:
        return "Command path too long (maximum 100 characters)"

    # Check for directory traversal
    if ".." in command_path or command_path.startswith("./"):
        return "Directory traversal is not allowed in commands"

    # Check for valid characters (alphanumeric, hyphens, underscores, forward slashes, colons)
    if not re.match(r"^[a-zA-Z0-9_/?:-]+$", command_path):
        return "Command contains invalid characters (only letters, numbers, hyphens, underscores, question marks, and forward slashes allowed)"

    # Check for too many nested levels (prevent deep directory traversal attempts)
    if command_path.count("/") > 5:
        return "Command path too deeply nested (maximum 5 levels)"

    # Validate path components don't escape root
    try:
        parts = PurePath(command_path).parts
        if ".." in parts or any(p.startswith("..") for p in parts):
            return "Directory traversal is not allowed in commands"

        # Verify the path stays within bounds
        normalized_parts: List[str] = []
        for part in parts:
            if part == "..":
                if normalized_parts:
                    normalized_parts.pop()
                else:
                    return "Directory traversal detected"
            elif part != ".":
                normalized_parts.append(part)

    except (ValueError, TypeError):
        return "Invalid command path format"

    return None  # Valid


def validate_raw_command_path(raw_command_path: str) -> Optional[str]:
    """Validate raw command path before sanitization.

    Args:
        raw_command_path: Raw command path from user input

    Returns:
        None if valid, error message if invalid
    """
    if error := _validate_common_security(raw_command_path):
        return error

    if error := _validate_control_chars(raw_command_path):
        return error

    if error := _validate_dangerous_chars(raw_command_path):
        return error

    # Check for absolute paths before sanitization
    if raw_command_path.startswith("/") or (len(raw_command_path) > 1 and raw_command_path[1] == ":"):
        return "Absolute paths are not allowed in commands"

    return None


def sanitize_command_path(command_path: str) -> str:
    """Sanitize command path by removing dangerous elements.

    Args:
        command_path: Raw command path

    Returns:
        Sanitized command path
    """
    # Remove any null bytes and control characters
    sanitized = "".join(char for char in command_path if ord(char) >= 32 and char != "\x7f")

    # Remove leading/trailing whitespace
    sanitized = sanitized.strip()

    # Normalize path separators
    sanitized = sanitized.replace("\\", "/")

    # Remove multiple consecutive slashes
    sanitized = re.sub(r"/+", "/", sanitized)

    # Remove leading slash if present (but keep the path for validation)
    if sanitized.startswith("/"):
        sanitized = sanitized[1:]

    return sanitized


def validate_command_path_full(raw_path: str) -> tuple[Optional[str], str]:
    """Validate and sanitize command path in one pass.

    Returns:
        Tuple of (error_message or None, sanitized_path)
    """
    # Step 1: Raw validation
    if error := validate_raw_command_path(raw_path):
        return error, ""

    # Step 2: Sanitize
    sanitized = sanitize_command_path(raw_path)

    # Step 3: Validate sanitized
    if error := validate_command_path(sanitized):
        return error, ""

    return None, sanitized
