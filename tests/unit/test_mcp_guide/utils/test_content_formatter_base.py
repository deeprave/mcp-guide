"""Tests for BaseFormatter."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_guide.utils.content_formatter_base import BaseFormatter
from mcp_guide.utils.file_discovery import FileInfo


class TestBaseFormatter:
    """Test BaseFormatter functionality."""

    @pytest.mark.asyncio
    async def test_format_empty_list(self):
        """Test format method with empty file list."""
        formatter = BaseFormatter()
        result = await formatter.format([], "test")
        assert result == ""

    @pytest.mark.asyncio
    async def test_format_single_file(self):
        """Test format method with single file."""
        formatter = BaseFormatter()
        file_info = FileInfo(
            path=Path("test.txt"),
            size=11,
            content_size=11,
            mtime=datetime.now(),
            name="test.txt",
            content="Hello World",
        )
        result = await formatter.format([file_info], "test")
        assert result == "Hello World"

    @pytest.mark.asyncio
    async def test_format_multiple_files(self):
        """Test format method with multiple files."""
        formatter = BaseFormatter()
        files = [
            FileInfo(
                path=Path("file1.txt"), size=5, content_size=5, mtime=datetime.now(), name="file1.txt", content="First"
            ),
            FileInfo(
                path=Path("file2.txt"), size=6, content_size=6, mtime=datetime.now(), name="file2.txt", content="Second"
            ),
        ]
        result = await formatter.format(files, "test")
        assert result == "First\nSecond"

    @pytest.mark.asyncio
    async def test_format_with_none_content(self):
        """Test format method handles None content."""
        formatter = BaseFormatter()
        files = [
            FileInfo(
                path=Path("file1.txt"), size=5, content_size=5, mtime=datetime.now(), name="file1.txt", content="First"
            ),
            FileInfo(
                path=Path("file2.txt"), size=0, content_size=0, mtime=datetime.now(), name="file2.txt", content=None
            ),
            FileInfo(
                path=Path("file3.txt"), size=5, content_size=5, mtime=datetime.now(), name="file3.txt", content="Third"
            ),
        ]
        result = await formatter.format(files, "test")
        assert result == "First\n\nThird"
