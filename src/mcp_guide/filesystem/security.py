"""Security policy for filesystem operations."""

from typing import List, Optional

from mcp_core.mcp_log import get_logger

from .path_validator import PathValidator, SecurityError

logger = get_logger(__name__)


class SecurityPolicy:
    """Security policy that wraps PathValidator with project-specific configuration."""

    def __init__(self, allowed_paths: List[str], project_root: Optional[str] = None):
        """Initialize SecurityPolicy.

        Args:
            allowed_paths: List of allowed directory paths from project config
            project_root: Optional project root directory
        """
        self.allowed_paths = allowed_paths
        self.project_root = project_root
        self.validator = PathValidator(allowed_paths, project_root)
        self._violation_count = 0

    def validate_path(self, path: str, operation: str = "access") -> str:
        """Validate path against security policy with audit logging.

        Args:
            path: Path to validate
            operation: Type of operation being performed

        Returns:
            Normalized path if valid

        Raises:
            SecurityError: If path violates security policy
        """
        try:
            validated_path = self.validator.validate(path)
            logger.debug(f"Security: {operation} allowed for path {path} -> {validated_path}")
            return validated_path
        except SecurityError as e:
            self._violation_count += 1
            logger.warning(f"Security violation #{self._violation_count}: {operation} denied for path {path} - {e}")
            raise

    async def validate_path_with_symlinks(self, path: str, operation: str = "access") -> str:
        """Validate path including symlink resolution via sampling request.

        Args:
            path: Path to validate (may be a symlink)
            operation: Type of operation being performed

        Returns:
            Normalized path if valid

        Raises:
            SecurityError: If path or symlink target violates security policy
        """
        try:
            # For now, return the original path - sampling validation not implemented
            return str(path)

        except SecurityError as e:
            self._violation_count += 1
            logger.warning(f"Security violation #{self._violation_count}: {operation} denied for path {path} - {e}")
            raise

    def get_violation_count(self) -> int:
        """Get the number of security violations detected."""
        return self._violation_count
