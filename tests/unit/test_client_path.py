"""Tests for client path resolution utilities."""

from pathlib import Path

import pytest

from mcp_guide.lazy_path import LazyPath
from mcp_guide.utils.client_path import client_resolve


class TestClientPathResolution:
    """Test client path resolution functionality."""

    @pytest.fixture(autouse=True)
    def verified_filesystem(self, monkeypatch):
        monkeypatch.setattr(LazyPath, "client_filesystem_shared", True)

    def test_client_resolve_relative_path(self):
        """Test resolving relative paths."""
        result = client_resolve(".guide.yaml", "/client/user/project")
        assert result == Path("/client/user/project/.guide.yaml")

    def test_client_resolve_relative_path_with_parent(self):
        """Test resolving relative paths with parent directory."""
        result = client_resolve("../config.json", "/client/user/project")
        assert result == Path("/client/user/config.json")

    def test_client_resolve_absolute_path(self):
        """Test resolving absolute paths (should return as-is)."""
        result = client_resolve("/absolute/path.txt", "/client/user/project")
        assert result == Path("/absolute/path.txt")

    def test_client_resolve_user_anchored_path(self, tmp_path, monkeypatch):
        """Test resolving a user-anchored path to an absolute client path."""
        home = tmp_path / "home"
        monkeypatch.setenv("HOME", str(home))

        assert client_resolve("~/file.txt", "/client/project") == home / "file.txt"

    def test_client_resolve_path_object_input(self):
        """Test resolving with Path object input."""
        result = client_resolve(Path("src/main.py"), "/client/user/project")
        assert result == Path("/client/user/project/src/main.py")

    def test_client_resolve_path_object_cwd(self):
        """Test resolving with Path object for client_cwd."""
        result = client_resolve("test.py", Path("/client/user/project"))
        assert result == Path("/client/user/project/test.py")

    def test_client_resolve_current_directory(self):
        """Test resolving current directory."""
        result = client_resolve(".", "/client/user/project")
        assert result == Path("/client/user/project/.")

    def test_client_resolve_nested_relative_path(self):
        """Test resolving nested relative paths."""
        result = client_resolve("src/utils/helper.py", "/client/user/project")
        assert result == Path("/client/user/project/src/utils/helper.py")
