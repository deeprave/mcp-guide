"""Tests for filesystem bridge file operation primitives."""

from unittest.mock import AsyncMock, Mock

import pytest

from mcp_guide.filesystem.filesystem_bridge import FilesystemBridge
from mcp_guide.filesystem.read_write_security import SecurityError


class TestFilesystemBridge:
    """Tests for FilesystemBridge class."""

    @pytest.fixture
    def mock_mcp_context(self):
        """Mock MCP context for sampling requests."""
        context = Mock()
        context.sample = AsyncMock()
        return context

    @pytest.fixture
    def bridge(self, mock_mcp_context):
        """FilesystemBridge instance with mocked context."""
        from mcp_guide.models import Project

        # Create a proper Project object with allowed paths
        project = Project(name="test-project", allowed_write_paths=["docs/", "openspec/"], additional_read_paths=[])
        return FilesystemBridge(project, mock_mcp_context)

    @pytest.mark.asyncio
    async def test_list_directory_basic(self, bridge, mock_mcp_context):
        """FilesystemBridge should list directory contents via sampling request."""
        # Mock sampling response - the bridge expects the response to contain the data directly
        mock_mcp_context.sample.return_value = [
            {"name": "readme.md", "type": "file", "size": 1024},
            {"name": "subdir", "type": "directory"},
        ]

        result = await bridge.list_directory("docs/")

        assert len(result) == 2
        assert result[0].name == "readme.md"
        assert result[0].type == "file"
        assert result[1].name == "subdir"
        assert result[1].type == "directory"

    @pytest.mark.asyncio
    async def test_read_file_basic(self, bridge, mock_mcp_context):
        """FilesystemBridge should read file content via sampling request."""
        # Mock sampling response
        mock_mcp_context.sample.return_value = "# Hello World\nThis is a test file."

        result = await bridge.read_file("docs/readme.md")

        assert result == "# Hello World\nThis is a test file."
        mock_mcp_context.sample.assert_called_once()

    @pytest.mark.asyncio
    async def test_path_validation_before_operations(self, bridge):
        """FilesystemBridge should validate paths before operations."""
        # list_directory should reject unsafe paths with a SecurityError
        with pytest.raises(SecurityError):
            await bridge.list_directory("../etc/")

        # read_file should also reject unsafe paths with a SecurityError
        with pytest.raises(SecurityError):
            await bridge.read_file("../etc/passwd")

    @pytest.mark.asyncio
    async def test_exception_handling_comprehensive(self, bridge, mock_mcp_context):
        """FilesystemBridge should handle various exception types correctly."""
        # Test UnicodeDecodeError propagation for binary files
        mock_mcp_context.sample.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")
        with pytest.raises(UnicodeDecodeError):
            await bridge.read_file("docs/binary-file.bin")

        # Test FileNotFoundError propagation
        mock_mcp_context.sample.side_effect = FileNotFoundError("File not found")
        with pytest.raises(FileNotFoundError):
            await bridge.read_file("docs/missing.txt")

        # Test PermissionError propagation
        mock_mcp_context.sample.side_effect = PermissionError("Permission denied")
        with pytest.raises(PermissionError):
            await bridge.read_file("docs/restricted.txt")

    @pytest.mark.asyncio
    async def test_list_directory_with_filter(self, bridge, mock_mcp_context):
        """FilesystemBridge should support directory listing with pattern filter."""
        mock_mcp_context.sample.return_value = [{"name": "test.md", "type": "file"}]

        result = await bridge.list_directory("docs/", pattern="*.md")

        assert len(result) == 1
        assert result[0].name == "test.md"

    @pytest.mark.asyncio
    async def test_read_file_with_encoding(self, bridge, mock_mcp_context):
        """FilesystemBridge should support reading files with specific encoding."""
        mock_mcp_context.sample.return_value = "UTF-8 content"

        result = await bridge.read_file("docs/file.txt", encoding="utf-8")

        assert result == "UTF-8 content"

    @pytest.mark.asyncio
    async def test_read_file_binary(self, bridge, mock_mcp_context):
        """FilesystemBridge should support reading binary files."""
        mock_mcp_context.sample.return_value = "SGVsbG8gV29ybGQ="  # "Hello World" in base64

        result = await bridge.read_file("docs/image.png", binary=True)

        assert result == "SGVsbG8gV29ybGQ="

    @pytest.mark.asyncio
    async def test_read_file_encoding_error_propagation(self, bridge, mock_mcp_context):
        """FilesystemBridge should propagate encoding errors for non-text files."""
        # Mock sampling request to raise UnicodeDecodeError
        mock_mcp_context.sample.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")

        with pytest.raises(UnicodeDecodeError):
            await bridge.read_file("docs/binary-file.bin", encoding="utf-8")

    @pytest.mark.asyncio
    async def test_discover_directories(self, bridge, mock_mcp_context):
        """FilesystemBridge should discover directory structure."""
        mock_mcp_context.sample.return_value = [
            {"name": "docs/", "type": "directory"},
            {"name": "docs/readme.md", "type": "file"},
            {"name": "src/", "type": "directory"},
            {"name": "src/main.py", "type": "file"},
        ]

        result = await bridge.discover_directories("docs/")

        assert len(result) == 2
        assert result[0].name == "docs/"
        assert result[0].type == "directory"
        assert result[1].name == "src/"
        assert result[1].type == "directory"
