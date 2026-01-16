"""Path security utilities for safe file access."""

from pathlib import Path

# System paths that should be blocked for security
SENSITIVE_SYSTEM_PATHS = {"/etc", "/proc", "/sys", "/dev", "/root", "/boot", "/var/log", "/usr/bin", "/bin", "/sbin"}


def resolve_safe_path(docroot: Path, path: str | Path) -> Path:
    """
    Resolve path within docroot with security validation.

    Args:
        docroot: Document root directory (must be absolute)
        path: Path to resolve (relative or absolute within docroot)

    Returns:
        Resolved absolute path within docroot

    Raises:
        ValueError: If docroot is not absolute
        ValueError: If path is absolute but not within docroot
        ValueError: If resolved path escapes docroot
    """
    # Validate docroot is absolute
    if not docroot.is_absolute():
        raise ValueError(f"Document root must be absolute: {docroot}")

    # Convert string to Path
    if isinstance(path, str):
        path = Path(path)

    # Handle absolute paths - check if within docroot
    if path.is_absolute():
        # Additional validation for sensitive system paths
        path_str = str(path).lower()
        if any(path_str.startswith(sensitive) for sensitive in SENSITIVE_SYSTEM_PATHS):
            raise ValueError(f"Access to system path denied: {path}")

        if not is_path_within_directory(path, docroot):
            raise ValueError(f"Absolute path must be within docroot: {path}")
        resolved = path.resolve()
    else:
        # Resolve relative path against docroot
        resolved = (docroot / path).resolve()

    # Final validation within bounds
    if not is_path_within_directory(resolved, docroot):
        raise ValueError(f"Path escapes docroot: {path}")

    return resolved


def is_path_within_directory(path: Path, directory: Path) -> bool:
    """
    Check if path is within directory bounds (after resolution).

    Args:
        path: Path to check (should be resolved/absolute)
        directory: Directory boundary (should be resolved/absolute)

    Returns:
        True if path is within directory
    """
    return path.resolve().is_relative_to(directory.resolve())
