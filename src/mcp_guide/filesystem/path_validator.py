"""Path validation for secure filesystem operations."""

from pathlib import Path, PurePath
from typing import List, Optional


class SecurityError(Exception):
    """Raised when a path violates security policy."""

    pass


class PathValidator:
    """Validates filesystem paths against security policy."""

    def __init__(self, allowed_paths: List[str], project_root: Optional[str] = None):
        """Initialize PathValidator.

        Args:
            allowed_paths: List of allowed directory paths (must end with '/')
            project_root: Optional project root directory for absolute path resolution
        """
        self.allowed_paths = [path.rstrip("/") + "/" for path in allowed_paths]
        self.project_root = Path(project_root) if project_root else Path.cwd()

    def validate(self, path: str) -> str:
        """Validate path against security policy.

        Args:
            path: Path to validate

        Returns:
            Normalized path if valid

        Raises:
            SecurityError: If path violates security policy
        """
        # Convert to Path for normalization
        path_obj = Path(path)

        # Handle absolute paths relative to project root
        if path_obj.is_absolute():
            try:
                path_obj = path_obj.relative_to(self.project_root)
            except ValueError:
                raise SecurityError(f"Absolute path {path} is outside project root")

        # Normalize the path (resolve . and .. components)
        normalized = str(PurePath(path_obj).as_posix())

        # Check for path traversal attempts
        if ".." in Path(normalized).parts:
            raise SecurityError(f"Path traversal detected in {path}")

        # Check if path is within allowed directories
        for allowed in self.allowed_paths:
            if normalized.startswith(allowed.rstrip("/")):
                return normalized

        raise SecurityError(f"Path {path} is outside allowed directories: {self.allowed_paths}")
