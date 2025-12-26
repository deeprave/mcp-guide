"""System directory blacklist for filesystem security."""

from pathlib import Path
from typing import List

# Dangerous system directories that should never be accessible for read operations
SYSTEM_DIRECTORY_BLACKLIST: List[str] = [
    # Unix/Linux system directories
    "/etc",
    "/usr/bin",
    "/usr/sbin",
    "/bin",
    "/sbin",
    "/boot",
    "/dev",
    "/proc",
    "/sys",
    "/root",
    # SSH key directories (Unix/Linux/macOS)
    "/home/*/.ssh",
    "/Users/*/.ssh",
    "/root/.ssh",
    # Windows system directories
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\System32",
    # Additional sensitive directories
    "/var/log",
    "/var/run",
    "/var/lib",
]


def is_system_directory(path: str) -> bool:
    """Check if path is in system directory blacklist.

    Args:
        path: Path to check (can be relative or absolute)

    Returns:
        True if path is a blacklisted system directory
    """
    path_obj = Path(path).resolve()
    path_posix = path_obj.as_posix()

    for blacklisted in SYSTEM_DIRECTORY_BLACKLIST:
        # Handle wildcard patterns like /home/*/.ssh
        if "*" in blacklisted:
            # Simple pattern matching for SSH directories
            if blacklisted == "/home/*/.ssh" and "/.ssh" in path_posix and "/home/" in path_posix:
                return True
            elif blacklisted == "/Users/*/.ssh" and "/.ssh" in path_posix and "/Users/" in path_posix:
                return True
        else:
            # Direct path comparison
            try:
                blacklisted_path = Path(blacklisted).resolve()
                # Check if path is within blacklisted directory
                path_obj.relative_to(blacklisted_path)
                return True
            except (ValueError, OSError):
                # Not within blacklisted directory or path doesn't exist
                continue

    return False
