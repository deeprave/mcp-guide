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


async def test_format_multiple_two_files():
    """Test formatting two files with separators."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    file1 = FileInfo(
        path=Path("docs/file1.md"),
        basename="file1.md",
        size=10,
        mtime=datetime.now(),
        content="Content 1",
    )
    file2 = FileInfo(
        path=Path("docs/file2.md"),
        basename="file2.md",
        size=10,
        mtime=datetime.now(),
        content="Content 2",
    )
    result = await formatter.format([file1, file2], "test")

    expected = "--- file1.md ---\nContent 1\n--- file2.md ---\nContent 2"
    assert result == expected


async def test_format_multiple_three_files():
    """Test formatting three files with separators."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    files = [
        FileInfo(
            path=Path(f"file{i}.md"),
            basename=f"file{i}.md",
            size=10,
            mtime=datetime.now(),
            content=f"Content {i}",
        )
        for i in range(1, 4)
    ]
    result = await formatter.format(files, "test")

    expected = "--- file1.md ---\nContent 1\n--- file2.md ---\nContent 2\n--- file3.md ---\nContent 3"
    assert result == expected


async def test_format_multiple_uses_basename():
    """Test that separator uses basename not full path."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    file1 = FileInfo(
        path=Path("docs/subdir/file.md"),
        basename="file.md",
        size=10,
        mtime=datetime.now(),
        content="Content",
    )
    file2 = FileInfo(
        path=Path("other/path/test.md"),
        basename="test.md",
        size=10,
        mtime=datetime.now(),
        content="Test",
    )
    result = await formatter.format([file1, file2], "test")

    assert "--- file.md ---" in result
    assert "--- test.md ---" in result
    assert "docs/subdir" not in result
    assert "other/path" not in result


async def test_format_multiple_preserves_content():
    """Test that content is preserved exactly in multiple files."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter

    formatter = PlainFormatter()
    content1 = "# Title\n\nWith **formatting**"
    content2 = "  Spaces  \n\tTabs\n"

    file1 = FileInfo(
        path=Path("file1.md"),
        basename="file1.md",
        size=len(content1),
        mtime=datetime.now(),
        content=content1,
    )
    file2 = FileInfo(
        path=Path("file2.md"),
        basename="file2.md",
        size=len(content2),
        mtime=datetime.now(),
        content=content2,
    )
    result = await formatter.format([file1, file2], "test")

    assert content1 in result
    assert content2 in result
