"""Tests for MIME content formatter."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_guide.utils.file_discovery import FileInfo


def test_module_imports():
    """Test that module can be imported."""
    from mcp_guide.utils import content_formatter_mime

    assert content_formatter_mime is not None


def test_mime_formatter_class_exists():
    """Test that MimeFormatter class exists."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    assert MimeFormatter is not None


def test_format_method_exists():
    """Test that format method exists."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    assert hasattr(formatter, "format")
    assert callable(formatter.format)


def test_format_single_method_exists():
    """Test that format_single method exists."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    assert hasattr(formatter, "format_single")
    assert callable(formatter.format_single)


async def test_format_empty_list():
    """Test that empty list returns empty string."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    result = await formatter.format([], "test-category")
    assert result == ""


async def test_format_single_file_delegates():
    """Test that single file delegates to format_single."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    file_info = FileInfo(
        path=Path("test.md"),
        basename="test.md",
        size=100,
        mtime=datetime.now(),
        content="test content",
    )
    result = await formatter.format([file_info], "test-category")
    # Should delegate to format_single and return formatted output
    assert "Content-Type:" in result
    assert "test content" in result


async def test_format_single_markdown_file():
    """Test formatting a single markdown file with MIME headers."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    content = "# Test\n\nThis is test content."
    file_info = FileInfo(
        path=Path("docs/test.md"),
        basename="test.md",
        size=len(content.encode("utf-8")),
        mtime=datetime.now(),
        content=content,
    )
    result = await formatter.format_single(file_info, "test-category")

    # Check headers are present
    assert "Content-Type: text/markdown" in result
    assert "Content-Location: guide://category/test-category/docs/test.md" in result
    assert f"Content-Length: {len(content.encode('utf-8'))}" in result

    # Check blank line separator and content
    assert "\r\n\r\n" in result
    assert result.endswith(content)


async def test_format_single_text_file():
    """Test formatting a text file."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    content = "Plain text content"
    file_info = FileInfo(
        path=Path("notes.txt"),
        basename="notes.txt",
        size=len(content.encode("utf-8")),
        mtime=datetime.now(),
        content=content,
    )
    result = await formatter.format_single(file_info, "docs")

    assert "Content-Type: text/plain" in result
    assert "Content-Location: guide://category/docs/notes.txt" in result


async def test_format_single_unknown_extension():
    """Test formatting file with unknown extension defaults to text/plain."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    content = "Unknown file type"
    file_info = FileInfo(
        path=Path("file.unknownext123"),
        basename="file.unknownext123",
        size=len(content.encode("utf-8")),
        mtime=datetime.now(),
        content=content,
    )
    result = await formatter.format_single(file_info, "misc")

    assert "Content-Type: text/plain" in result


async def test_format_single_utf8_content():
    """Test Content-Length correctly counts UTF-8 bytes."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    content = "Hello 世界 🌍"  # Multi-byte characters
    file_info = FileInfo(
        path=Path("unicode.txt"),
        basename="unicode.txt",
        size=len(content.encode("utf-8")),
        mtime=datetime.now(),
        content=content,
    )
    result = await formatter.format_single(file_info, "test")

    byte_count = len(content.encode("utf-8"))
    assert f"Content-Length: {byte_count}" in result
    assert byte_count > len(content)  # Verify multi-byte counting
