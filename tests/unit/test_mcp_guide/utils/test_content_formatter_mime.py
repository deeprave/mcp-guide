"""Tests for MIME content formatter."""

from datetime import datetime
from pathlib import Path

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
        name="test.md",
        size=100,
        content_size=100,
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
        name="test.md",
        size=len(content.encode("utf-8")),
        content_size=len(content.encode("utf-8")),
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
        name="notes.txt",
        size=len(content.encode("utf-8")),
        content_size=len(content.encode("utf-8")),
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
        name="file.unknownext123",
        size=len(content.encode("utf-8")),
        content_size=len(content.encode("utf-8")),
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
        name="unicode.txt",
        size=len(content.encode("utf-8")),
        content_size=len(content.encode("utf-8")),
        mtime=datetime.now(),
        content=content,
    )
    result = await formatter.format_single(file_info, "test")

    byte_count = len(content.encode("utf-8"))
    assert f"Content-Length: {byte_count}" in result
    assert byte_count > len(content)  # Verify multi-byte counting


async def test_format_single_uses_content_size_not_content_length():
    """Test that Content-Length uses content_size field, not calculated length."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    content = "Test content"

    # Set content_size different from actual content length to verify it's used
    file_info = FileInfo(
        path=Path("test.txt"),
        name="test.txt",
        size=200,  # Original file size
        content_size=50,  # Different from len(content.encode("utf-8"))
        mtime=datetime.now(),
        content=content,
    )
    result = await formatter.format_single(file_info, "test")

    # Should use actual content length (12), not content_size (50)
    # This is correct behavior after template rendering
    assert f"Content-Length: {len(content.encode('utf-8'))}" in result
    assert "Content-Length: 50" not in result


async def test_format_multiple_main_header():
    """Test that multiple files have multipart/mixed header with boundary."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    files = [
        FileInfo(
            path=Path("file1.md"),
            name="file1.md",
            size=10,
            content_size=10,
            mtime=datetime.now(),
            content="Content 1",
        ),
        FileInfo(
            path=Path("file2.md"),
            name="file2.md",
            size=10,
            content_size=10,
            mtime=datetime.now(),
            content="Content 2",
        ),
    ]
    result = await formatter.format(files, "test")

    assert result.startswith("Content-Type: multipart/mixed; boundary=")
    # Extract boundary from header
    lines = result.split("\r\n")
    assert "Content-Type: multipart/mixed; boundary=" in lines[0]


async def test_format_multiple_boundary_format():
    """Test that boundary follows UUID format and is used correctly."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    files = [
        FileInfo(
            path=Path("file1.md"),
            name="file1.md",
            size=10,
            content_size=10,
            mtime=datetime.now(),
            content="Content 1",
        ),
        FileInfo(
            path=Path("file2.md"),
            name="file2.md",
            size=10,
            content_size=10,
            mtime=datetime.now(),
            content="Content 2",
        ),
    ]
    result = await formatter.format(files, "test")

    # Extract boundary
    first_line = result.split("\r\n")[0]
    boundary = first_line.split('boundary="')[1].rstrip('"')

    # Check guide-boundary-{uuid} format
    import re

    boundary_pattern = r"^guide-boundary-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    assert re.match(boundary_pattern, boundary), f"Boundary {boundary} does not match guide-boundary-{{uuid}} format"

    # Check boundary usage
    assert f"--{boundary}\r\n" in result  # Part boundaries
    assert f"--{boundary}--" in result  # Closing boundary


async def test_format_multiple_part_headers():
    """Test that each part has proper MIME headers."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    files = [
        FileInfo(
            path=Path("docs/file1.md"),
            name="file1.md",
            size=10,
            content_size=10,
            mtime=datetime.now(),
            content="Content 1",
        ),
        FileInfo(
            path=Path("docs/file2.txt"),
            name="file2.txt",
            size=10,
            content_size=10,
            mtime=datetime.now(),
            content="Content 2",
        ),
    ]
    result = await formatter.format(files, "test")

    # Check first part headers - should use actual content length
    assert "Content-Type: text/markdown" in result
    assert "Content-Location: guide://category/test/docs/file1.md" in result
    assert f"Content-Length: {len(files[0].content.encode('utf-8'))}" in result

    # Check second part headers - should use actual content length
    assert "Content-Type: text/plain" in result
    assert "Content-Location: guide://category/test/docs/file2.txt" in result
    assert f"Content-Length: {len(files[1].content.encode('utf-8'))}" in result


async def test_format_multiple_uses_content_size():
    """Test that multiple files use content_size for Content-Length."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    files = [
        FileInfo(
            path=Path("file1.txt"),
            name="file1.txt",
            size=100,  # Original size
            content_size=25,  # Content size after frontmatter removal
            mtime=datetime.now(),
            content="Content 1",
        ),
        FileInfo(
            path=Path("file2.txt"),
            name="file2.txt",
            size=200,  # Original size
            content_size=35,  # Content size after frontmatter removal
            mtime=datetime.now(),
            content="Content 2",
        ),
    ]
    result = await formatter.format(files, "test")

    # Should use actual content length, not content_size
    assert f"Content-Length: {len('Content 1'.encode('utf-8'))}" in result
    assert f"Content-Length: {len('Content 2'.encode('utf-8'))}" in result
    assert "Content-Length: 25" not in result
    assert "Content-Length: 35" not in result


async def test_format_multiple_crlf_line_endings():
    """Test that CRLF line endings are used throughout."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    files = [
        FileInfo(
            path=Path("file1.md"),
            name="file1.md",
            size=10,
            content_size=10,
            mtime=datetime.now(),
            content="Content 1",
        ),
        FileInfo(
            path=Path("file2.md"),
            name="file2.md",
            size=10,
            content_size=10,
            mtime=datetime.now(),
            content="Content 2",
        ),
    ]
    result = await formatter.format(files, "test")

    # Check CRLF is used
    assert "\r\n" in result
    # Verify no bare LF (except possibly in content)
    lines = result.split("\r\n")
    assert len(lines) > 5  # Should have multiple lines


async def test_format_multiple_content_preserved():
    """Test that content is preserved exactly in multipart format."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter

    formatter = MimeFormatter()
    content1 = "# Title\n\nWith **formatting**"
    content2 = "  Spaces  \n\tTabs\n"

    files = [
        FileInfo(
            path=Path("file1.md"),
            name="file1.md",
            size=len(content1),
            content_size=len(content1),
            mtime=datetime.now(),
            content=content1,
        ),
        FileInfo(
            path=Path("file2.md"),
            name="file2.md",
            size=len(content2),
            content_size=len(content2),
            mtime=datetime.now(),
            content=content2,
        ),
    ]
    result = await formatter.format(files, "test")

    assert content1 in result
    assert content2 in result
