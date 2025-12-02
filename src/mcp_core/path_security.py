"""Path security utilities for safe file access."""

from pathlib import Path


def resolve_safe_path(base_dir: Path, relative_path: str | Path) -> Path:
    """
    Resolve relative path within base directory with security validation.

    Args:
        base_dir: Base directory (must be absolute)
        relative_path: Relative path to resolve

    Returns:
        Resolved absolute path within base_dir

    Raises:
        ValueError: If base_dir is not absolute
        ValueError: If relative_path is absolute
        ValueError: If resolved path escapes base_dir
    """
    # Validate base_dir is absolute
    if not base_dir.is_absolute():
        raise ValueError(f"Base directory must be absolute: {base_dir}")

    # Convert string to Path
    if isinstance(relative_path, str):
        relative_path = Path(relative_path)

    # Reject absolute paths
    if relative_path.is_absolute():
        raise ValueError(f"Path must be relative: {relative_path}")

    # Resolve path (handles ., .., symlinks, //)
    resolved = (base_dir / relative_path).resolve()

    # Validate within bounds
    if not is_path_within_directory(resolved, base_dir):
        raise ValueError(f"Path escapes base directory: {relative_path}")

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
