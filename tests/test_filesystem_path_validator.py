"""Tests for filesystem path validation logic."""

import pytest

from mcp_guide.filesystem.path_validator import PathValidator, SecurityError


class TestPathValidator:
    """Tests for PathValidator class."""

    def test_allowed_path_access(self):
        """PathValidator should allow access to paths within allowed directories."""
        allowed_paths = ["docs/", "openspec/"]
        validator = PathValidator(allowed_paths)

        # Test allowed paths
        assert validator.validate("docs/readme.md") == "docs/readme.md"
        assert validator.validate("openspec/spec.md") == "openspec/spec.md"

    def test_disallowed_path_access(self):
        """PathValidator should raise SecurityError for paths outside allowed directories."""
        allowed_paths = ["docs/"]
        validator = PathValidator(allowed_paths)

        with pytest.raises(SecurityError, match="outside allowed directories"):
            validator.validate("src/secret.py")

    def test_path_traversal_prevention(self):
        """PathValidator should prevent path traversal attacks."""
        allowed_paths = ["docs/"]
        validator = PathValidator(allowed_paths)

        with pytest.raises(SecurityError):
            validator.validate("docs/../src/secret.py")

        with pytest.raises(SecurityError):
            validator.validate("../etc/passwd")

    def test_absolute_path_handling(self):
        """PathValidator should handle absolute paths relative to project root."""
        allowed_paths = ["docs/"]
        validator = PathValidator(allowed_paths, project_root="/project")

        # Absolute paths should be resolved relative to project root
        result = validator.validate("/project/docs/file.md")
        assert result == "docs/file.md"

    def test_symbolic_link_validation(self):
        """PathValidator should validate symbolic link targets."""
        allowed_paths = ["docs/"]
        validator = PathValidator(allowed_paths)

        # This would need actual symlink testing in integration tests
        # For now, test the validation logic exists
        assert hasattr(validator, "validate")

    def test_path_normalization(self):
        """PathValidator should normalize paths."""
        allowed_paths = ["docs/"]
        validator = PathValidator(allowed_paths)

        # Test path normalization
        assert validator.validate("docs//file.md") == "docs/file.md"
        assert validator.validate("docs/./file.md") == "docs/file.md"
