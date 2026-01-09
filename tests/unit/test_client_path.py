"""Tests for client path resolution utilities."""

from pathlib import Path

from mcp_guide.utils.client_path import client_resolve


class TestClientPathResolution:
    """Test client path resolution functionality."""

    def test_client_resolve_relative_path(self):
        """Test resolving relative paths."""
        result = client_resolve(".guide.yaml", "/home/username/project")
        assert result == Path("/home/username/project/.guide.yaml")

    def test_client_resolve_relative_path_with_parent(self):
        """Test resolving relative paths with parent directory."""
        result = client_resolve("../config.json", "/home/username/project")
        assert result == Path("/home/username/project/../config.json")

    def test_client_resolve_absolute_path(self):
        """Test resolving absolute paths (should return as-is)."""
        result = client_resolve("/absolute/path.txt", "/home/username/project")
        assert result == Path("/absolute/path.txt")

    def test_client_resolve_path_object_input(self):
        """Test resolving with Path object input."""
        result = client_resolve(Path("src/main.py"), "/home/username/project")
        assert result == Path("/home/username/project/src/main.py")

    def test_client_resolve_path_object_cwd(self):
        """Test resolving with Path object for client_cwd."""
        result = client_resolve("test.py", Path("/home/username/project"))
        assert result == Path("/home/username/project/test.py")

    def test_client_resolve_current_directory(self):
        """Test resolving current directory."""
        result = client_resolve(".", "/home/username/project")
        assert result == Path("/home/username/project/.")

    def test_client_resolve_nested_relative_path(self):
        """Test resolving nested relative paths."""
        result = client_resolve("src/utils/helper.py", "/home/username/project")
        assert result == Path("/home/username/project/src/utils/helper.py")
