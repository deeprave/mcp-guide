"""Integration tests for content_size in MIME formatter."""

from datetime import datetime
from pathlib import Path

from mcp_guide.utils.content_formatter_mime import MimeFormatter
from mcp_guide.utils.file_discovery import FileInfo


async def test_mime_formatter_uses_content_size_single_file():
    """Test MIME formatter uses content_size for single file Content-Length."""
    content = "Test content"
    original_size = 100  # Simulates original file size with frontmatter
    content_size = len(content.encode("utf-8"))  # Size after frontmatter removal

    file_info = FileInfo(
        path=Path("test.txt"),
        name="test.txt",
        size=original_size,
        content_size=content_size,
        mtime=datetime.now(),
        content=content,
    )

    formatter = MimeFormatter()
    result = await formatter.format_single(file_info, "test")

    # Should use content_size (12), not original size (100)
    assert f"Content-Length: {content_size}" in result
    assert f"Content-Length: {original_size}" not in result
    assert content in result


async def test_mime_formatter_uses_content_size_multiple_files():
    """Test MIME formatter uses content_size for multiple files Content-Length."""
    files = [
        FileInfo(
            path=Path("file1.txt"),
            name="file1.txt",
            size=200,  # Original size with frontmatter
            content_size=50,  # Size after frontmatter removal
            mtime=datetime.now(),
            content="File 1 content",
        ),
        FileInfo(
            path=Path("file2.txt"),
            name="file2.txt",
            size=300,  # Original size with frontmatter
            content_size=75,  # Size after frontmatter removal
            mtime=datetime.now(),
            content="File 2 content",
        ),
    ]

    formatter = MimeFormatter()
    result = await formatter.format(files, "test")

    # Should use content_size values
    assert "Content-Length: 50" in result
    assert "Content-Length: 75" in result

    # Should NOT use original sizes
    assert "Content-Length: 200" not in result
    assert "Content-Length: 300" not in result

    # Should NOT calculate from actual content
    assert f"Content-Length: {len('File 1 content'.encode('utf-8'))}" not in result
    assert f"Content-Length: {len('File 2 content'.encode('utf-8'))}" not in result


async def test_content_size_equals_size_when_no_frontmatter():
    """Test that when content_size equals size, behavior is correct."""
    content = "No frontmatter here"
    size = len(content.encode("utf-8"))

    file_info = FileInfo(
        path=Path("plain.txt"),
        name="plain.txt",
        size=size,
        content_size=size,  # Same as size when no frontmatter
        mtime=datetime.now(),
        content=content,
    )

    formatter = MimeFormatter()
    result = await formatter.format_single(file_info, "test")

    # Should use content_size (which equals size in this case)
    assert f"Content-Length: {size}" in result
    assert content in result


async def test_content_size_different_from_calculated_length():
    """Test edge case where content_size differs from calculated content length."""
    # This could happen if content was modified after content_size was set
    content = "Modified content"
    content_size = 25  # Different from actual content length

    file_info = FileInfo(
        path=Path("modified.txt"),
        name="modified.txt",
        size=100,
        content_size=content_size,
        mtime=datetime.now(),
        content=content,
    )

    formatter = MimeFormatter()
    result = await formatter.format_single(file_info, "test")

    # Should use content_size field, not calculate from content
    assert f"Content-Length: {content_size}" in result
    assert f"Content-Length: {len(content.encode('utf-8'))}" not in result
    assert content in result
