"""Tests for filesystem MCP tools."""

from unittest.mock import patch

import pytest

from mcp_guide.tools.tool_filesystem import (
    SendCommandLocationArgs,
    SendDirectoryListingArgs,
    SendFileContentArgs,
    SendWorkingDirectoryArgs,
    internal_send_command_location,
    internal_send_directory_listing,
    internal_send_file_content,
    internal_send_working_directory,
)


class TestSendFileContentTool:
    """Tests for internal_send_file_content function."""

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_file_content")
    async def test_send_file_content_success(self, mock_send):
        """internal_send_file_content should call underlying function."""
        mock_send.return_value = {
            "success": True,
            "message": "File cached successfully",
            "path": "docs/readme.md",
            "size": 25,
        }

        args = SendFileContentArgs(path="docs/readme.md", content="# Hello World\nThis is a test file.")

        result = await internal_send_file_content(args)

        assert result.success is True
        assert result.value["message"] == "File cached successfully"
        assert result.value["path"] == "docs/readme.md"
        assert result.value["size"] == 25

        mock_send.assert_called_once_with(
            context=None,
            path="docs/readme.md",
            content="# Hello World\nThis is a test file.",
            mtime=None,
            encoding="utf-8",
        )

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_file_content")
    async def test_send_file_content_error(self, mock_send):
        """internal_send_file_content should handle errors."""
        mock_send.side_effect = Exception("Test error")

        args = SendFileContentArgs(path="docs/readme.md", content="content")

        result = await internal_send_file_content(args)

        assert result.success is False
        assert result.error_type == "unknown"
        assert "Test error" in result.error


class TestSendDirectoryListingTool:
    """Tests for internal_send_directory_listing function."""

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_directory_listing")
    async def test_send_directory_listing_success(self, mock_send):
        """internal_send_directory_listing should call underlying function."""
        entries = [
            {"name": "readme.md", "type": "file", "size": 1024, "mtime": 1234567890.0},
            {"name": "subdir", "type": "directory", "size": 0, "mtime": 1234567890.0},
        ]

        mock_send.return_value = {
            "success": True,
            "message": "Directory listing cached",
            "path": "docs/",
            "entries": entries,
        }

        args = SendDirectoryListingArgs(path="docs/", entries=entries)

        result = await internal_send_directory_listing(args)

        assert result.success is True
        assert result.value["message"] == "Directory listing cached"
        assert result.value["path"] == "docs/"
        assert len(result.value["entries"]) == 2

        mock_send.assert_called_once_with(context=None, path="docs/", files=entries)

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_directory_listing")
    async def test_send_directory_listing_error(self, mock_send):
        """internal_send_directory_listing should handle errors."""
        mock_send.side_effect = Exception("Test error")

        args = SendDirectoryListingArgs(path="docs/", entries=[])

        result = await internal_send_directory_listing(args)

        assert result.success is False
        assert result.error_type == "unknown"
        assert "Test error" in result.error


class TestSendCommandLocationTool:
    """Tests for internal_send_command_location function."""

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_command_location")
    async def test_send_command_location_success_found(self, mock_send):
        """internal_send_command_location should handle found commands."""
        mock_send.return_value = {
            "success": True,
            "message": "Command location cached",
            "command": "python",
            "location": "/usr/bin/python",
        }

        args = SendCommandLocationArgs(command="python", location="/usr/bin/python")

        result = await internal_send_command_location(args)

        assert result.success is True
        assert result.value["command"] == "python"
        assert result.value["location"] == "/usr/bin/python"

        mock_send.assert_called_once_with(
            context=None,
            command="python",
            path="/usr/bin/python",
            found=True,
        )

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_command_location")
    async def test_send_command_location_success_not_found(self, mock_send):
        """internal_send_command_location should handle missing commands."""
        mock_send.return_value = {
            "success": True,
            "message": "Command not found",
            "command": "nonexistent",
            "location": None,
        }

        args = SendCommandLocationArgs(command="nonexistent", location=None)

        result = await internal_send_command_location(args)

        assert result.success is True
        assert result.value["command"] == "nonexistent"
        assert result.value["location"] is None

        mock_send.assert_called_once_with(
            context=None,
            command="nonexistent",
            path=None,
            found=False,
        )

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_command_location")
    async def test_send_command_location_error(self, mock_send):
        """internal_send_command_location should handle errors."""
        mock_send.side_effect = Exception("Test error")

        args = SendCommandLocationArgs(command="python", location="/usr/bin/python")

        result = await internal_send_command_location(args)

        assert result.success is False
        assert result.error_type == "unknown"
        assert "Test error" in result.error


class TestSendWorkingDirectoryTool:
    """Tests for internal_send_working_directory function."""

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_working_directory")
    async def test_send_working_directory_success(self, mock_send):
        """internal_send_working_directory should call underlying function."""
        mock_send.return_value = {
            "success": True,
            "message": "Working directory cached",
            "path": "/home/user/project",
        }

        args = SendWorkingDirectoryArgs(path="/home/user/project")

        result = await internal_send_working_directory(args)

        assert result.success is True
        assert result.value["message"] == "Working directory cached"
        assert result.value["path"] == "/home/user/project"

        mock_send.assert_called_once_with(
            context=None,
            working_directory="/home/user/project",
        )

    @pytest.mark.asyncio
    @patch("mcp_guide.tools.tool_filesystem.fs_send_working_directory")
    async def test_send_working_directory_error(self, mock_send):
        """internal_send_working_directory should handle errors."""
        mock_send.side_effect = Exception("Test error")

        args = SendWorkingDirectoryArgs(path="/home/user/project")

        result = await internal_send_working_directory(args)

        assert result.success is False
        assert result.error_type == "unknown"
        assert "Test error" in result.error
