"""Temporary directory validation for safe write operations."""

import os
from pathlib import Path


def is_safe_temp_path(path: Path) -> bool:
    """Check if path is a safe temporary directory for write operations.

    Args:
        path: Path to validate

    Returns:
        True if path is a safe temporary directory
    """
    path_posix = path.as_posix()

    # Check for standard temp directory patterns
    if any(part.lower() in ("tmp", "temp") for part in path.parts):
        return True

    # Check for environment variable temp directories
    for env_var in ["TMPDIR", "TEMP", "TMP"]:
        env_path = os.environ.get(env_var)
        if env_path and env_path.strip() and path_posix.startswith(env_path):
            return True

    # Check for standard cache directories
    if "/.cache/" in path_posix or path.name == ".cache":
        return True

    return False
