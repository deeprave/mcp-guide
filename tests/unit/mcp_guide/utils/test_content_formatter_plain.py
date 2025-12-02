"""Tests for plain content formatter."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_guide.utils.file_discovery import FileInfo


def test_module_imports():
    """Test that module can be imported."""
    from mcp_guide.utils import content_formatter_plain

    assert content_formatter_plain is not None


def test_plain_formatter_class_exists():
    """Test that PlainFormatter class exists."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    assert PlainFormatter is not None


def test_format_method_exists():
    """Test that format method exists."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    assert hasattr(formatter, "format")
    assert callable(formatter.format)


def test_format_single_method_exists():
    """Test that format_single method exists."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    assert hasattr(formatter, "format_single")
    assert callable(formatter.format_single)


async def test_format_empty_list():
    """Test that empty list returns empty string."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    result = await formatter.format([], "test-category")
    assert result == ""


async def test_format_single_file_returns_content():
    """Test that single file returns content unchanged."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    content = "# Test\n\nThis is test content."
    file_info = FileInfo(
        path=Path("test.md"),
        basename="test.md",
        size=len(content.encode("utf-8")),
        mtime=datetime.now(),
        content=content,
    )
    result = await formatter.format([file_info], "test-category")
    assert result == content


async def test_format_single_preserves_line_endings():
    """Test that line endings are preserved."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    content = "Line 1\nLine 2\r\nLine 3\n"
    file_info = FileInfo(
        path=Path("test.txt"),
        basename="test.txt",
        size=len(content.encode("utf-8")),
        mtime=datetime.now(),
        content=content,
    )
    result = await formatter.format_single(file_info, "test")
    assert result == content


async def test_format_single_preserves_whitespace():
    """Test that whitespace is preserved."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    content = "  Leading spaces\n\tTabs\n  Trailing  "
    file_info = FileInfo(
        path=Path("test.txt"),
        basename="test.txt",
        size=len(content.encode("utf-8")),
        mtime=datetime.now(),
        content=content,
    )
    result = await formatter.format_single(file_info, "test")
    assert result == content


async def test_format_single_no_headers():
    """Test that no headers are added."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    content = "Plain content"
    file_info = FileInfo(
        path=Path("test.md"),
        basename="test.md",
        size=len(content.encode("utf-8")),
        mtime=datetime.now(),
        content=content,
    )
    result = await formatter.format_single(file_info, "test")
    # Verify no MIME headers
    assert "Content-Type:" not in result
    assert "Content-Location:" not in result
    assert "Content-Length:" not in result
    assert "\r\n\r\n" not in result
    assert result == content


async def test_format_single_empty_file():
    """Test that empty files work correctly."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    file_info = FileInfo(
        path=Path("empty.txt"),
        basename="empty.txt",
        size=0,
        mtime=datetime.now(),
        content="",
    )
    result = await formatter.format_single(file_info, "test")
    assert result == ""


async def test_format_single_none_content():
    """Test that None content returns empty string."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    file_info = FileInfo(
        path=Path("test.txt"),
        basename="test.txt",
        size=0,
        mtime=datetime.now(),
        content=None,
    )
    result = await formatter.format_single(file_info, "test")
    assert result == ""


async def test_format_multiple_files_placeholder():
    """Test that multiple files returns empty string (placeholder for future)."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    file_info1 = FileInfo(
        path=Path("test1.md"),
        basename="test1.md",
        size=10,
        mtime=datetime.now(),
        content="Content 1",
    )
    file_info2 = FileInfo(
        path=Path("test2.md"),
        basename="test2.md",
        size=10,
        mtime=datetime.now(),
        content="Content 2",
    )
    result = await formatter.format([file_info1, file_info2], "test")
    assert result == ""
