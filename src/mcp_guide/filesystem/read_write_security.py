"""Read/Write security policy for filesystem operations."""

import logging
from pathlib import Path, PurePath
from typing import List, Optional

from .system_directories import is_system_directory
from .temp_directories import is_safe_temp_path

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when a path violates security policy."""

    pass


class ReadWriteSecurityPolicy:
    """Security policy with separate read and write permissions."""

    def __init__(
        self,
        write_allowed_paths: Optional[List[str]] = None,
        additional_read_paths: Optional[List[str]] = None,
        project_root: Optional[str] = None,
    ):
        """Initialize security policy.

        Args:
            write_allowed_paths: Relative paths allowed for write operations
            additional_read_paths: Absolute paths allowed for read operations
            project_root: Optional project root for path resolution
        """
        self.write_allowed_paths = [path.rstrip("/") + "/" for path in (write_allowed_paths or [])]
        self.additional_read_paths = additional_read_paths or []
        self.project_root = Path(project_root) if project_root else None
        self._violation_count = 0

    def set_project_root(self, project_root: str) -> None:
        """Inject project root once discovered."""
        self.project_root = Path(project_root)

    def validate_read_path(self, path: str) -> str:
        """Validate path for read operations.

        Args:
            path: Path to validate

        Returns:
            Normalized path if valid

        Raises:
            SecurityError: If path violates read security policy
        """
        path_obj = Path(path)

        # Handle absolute paths
        if path_obj.is_absolute():
            # Check if it's in additional read paths
            path_posix = path_obj.as_posix()
            for allowed_abs in self.additional_read_paths:
                if path_posix.startswith(allowed_abs.rstrip("/") + "/") or path_posix == allowed_abs.rstrip("/"):
                    # Check system directory blacklist
                    if is_system_directory(path):
                        self._violation_count += 1
                        logger.warning(
                            f"Security violation #{self._violation_count}: read denied for system directory {path}"
                        )
                        raise SecurityError(f"System directory access denied: {path}")
                    return str(path_obj)

            # If project root is known, check if absolute path is within project
            if self.project_root:
                try:
                    rel_path = path_obj.relative_to(self.project_root)
                    return self._validate_relative_read_path(str(rel_path))
                except ValueError:
                    pass

            # Absolute path not in allowed additional paths
            self._violation_count += 1
            logger.warning(f"Security violation #{self._violation_count}: read denied for absolute path {path}")
            raise SecurityError(f"Absolute path not in additional_read_paths: {path}")

        # Handle relative paths - assume allowed (project boundary checked when root known)
        return self._validate_relative_read_path(path)

    def _validate_relative_read_path(self, path: str) -> str:
        """Validate relative path for read operations."""
        # Normalize the path (resolve . and .. components)
        normalized = str(PurePath(path).as_posix())

        # Check for path traversal attempts
        if ".." in Path(normalized).parts:
            self._violation_count += 1
            logger.warning(f"Security violation #{self._violation_count}: path traversal detected in {path}")
            raise SecurityError(f"Path traversal detected in {path}")

        return normalized

    def validate_write_path(self, path: str) -> str:
        """Validate path for write operations.

        Args:
            path: Path to validate

        Returns:
            Normalized path if valid

        Raises:
            SecurityError: If path violates write security policy
        """
        path_obj = Path(path)

        # Handle absolute paths - not allowed for write unless temp
        if path_obj.is_absolute():
            # Check if it's a safe temporary directory
            if is_safe_temp_path(path_obj):
                logger.debug(f"Write allowed to temporary directory: {path}")
                return str(path_obj)
            else:
                self._violation_count += 1
                logger.warning(f"Security violation #{self._violation_count}: write denied for absolute path {path}")
                raise SecurityError(f"Write to absolute path not allowed: {path}")

        # Handle relative paths - must be in allowed write paths
        normalized = str(PurePath(path).as_posix())

        # Check for path traversal attempts
        if ".." in Path(normalized).parts:
            self._violation_count += 1
            logger.warning(f"Security violation #{self._violation_count}: path traversal detected in {path}")
            raise SecurityError(f"Path traversal detected in {path}")

        # Check if it's a safe temporary directory (for relative paths too)
        if is_safe_temp_path(Path(normalized)):
            logger.debug(f"Write allowed to temporary directory: {path}")
            return normalized

        # Check if path is within allowed write directories
        for allowed in self.write_allowed_paths:
            allowed_prefix = allowed.rstrip("/") + "/"
            if normalized.startswith(allowed_prefix):
                logger.debug(f"Write allowed for path {path} -> {normalized}")
                return normalized

        self._violation_count += 1
        logger.warning(f"Security violation #{self._violation_count}: write denied for path {path}")
        raise SecurityError(f"Path {path} is outside allowed write directories: {self.write_allowed_paths}")

    def get_violation_count(self) -> int:
        """Get the number of security violations detected."""
        return self._violation_count
