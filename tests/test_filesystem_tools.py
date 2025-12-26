"""Tests for filesystem MCP tools."""

from unittest.mock import patch

import pytest

from mcp_guide.tools.tool_filesystem import (
    SendDirectoryListingArgs,
    SendFileContentArgs,
    internal_send_directory_listing,
    internal_send_file_content,
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
