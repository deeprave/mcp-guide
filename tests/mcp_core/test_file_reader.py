"""Tests for file_reader module."""

from pathlib import Path

import pytest

from mcp_core.file_reader import read_file_content


@pytest.mark.asyncio
async def test_read_utf8_file(tmp_path: Path) -> None:
    """Test reading UTF-8 text file."""
    file = tmp_path / "test.txt"
    content = "Hello, World!\n"
    file.write_text(content)

    result = await read_file_content(file)

    assert result == content


@pytest.mark.asyncio
async def test_read_empty_file(tmp_path: Path) -> None:
    """Test reading empty file."""
    file = tmp_path / "empty.txt"
    file.touch()

    result = await read_file_content(file)

    assert result == ""


@pytest.mark.asyncio
async def test_preserves_line_endings_and_whitespace(tmp_path: Path) -> None:
    """Test that line endings and whitespace are preserved."""
    file = tmp_path / "whitespace.txt"
    content = "Line 1\n  Line 2 with spaces  \n\nLine 4\n"
    file.write_text(content)

    result = await read_file_content(file)

    assert result == content


@pytest.mark.asyncio
async def test_binary_file_raises_error(tmp_path: Path) -> None:
    """Test that binary files raise UnicodeDecodeError."""
    file = tmp_path / "binary.bin"
    file.write_bytes(b"\x00\x01\x02\x03\xff\xfe")

    with pytest.raises(UnicodeDecodeError):
        await read_file_content(file)


@pytest.mark.asyncio
async def test_invalid_utf8_raises_error(tmp_path: Path) -> None:
    """Test that invalid UTF-8 raises UnicodeDecodeError."""
    file = tmp_path / "invalid.txt"
    # Write invalid UTF-8 sequence
    file.write_bytes(b"Valid text \xc3\x28 invalid")

    with pytest.raises(UnicodeDecodeError):
        await read_file_content(file)


@pytest.mark.asyncio
async def test_permission_error(tmp_path: Path) -> None:
    """Test that permission errors are raised."""
    file = tmp_path / "noperm.txt"
    file.write_text("content")
    file.chmod(0o000)  # Remove all permissions

    try:
        with pytest.raises(PermissionError):
            await read_file_content(file)
    finally:
        file.chmod(0o644)  # Restore for cleanup


@pytest.mark.asyncio
async def test_missing_file_raises_error(tmp_path: Path) -> None:
    """Test that missing files raise FileNotFoundError."""
    file = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        await read_file_content(file)


@pytest.mark.asyncio
async def test_large_file(tmp_path: Path) -> None:
    """Test reading large file (1MB)."""
    file = tmp_path / "large.txt"
    content = "x" * (1024 * 1024)  # 1MB
    file.write_text(content)

    result = await read_file_content(file)

    assert len(result) == len(content)


@pytest.mark.asyncio
async def test_unicode_content(tmp_path: Path) -> None:
    """Test reading file with Unicode characters."""
    file = tmp_path / "unicode.txt"
    content = "Hello 世界 🌍\n"
    file.write_text(content)

    result = await read_file_content(file)

    assert result == content


@pytest.mark.asyncio
async def test_various_line_endings(tmp_path: Path) -> None:
    """Test files with different line endings."""
    file = tmp_path / "mixed.txt"
    # Python normalizes to \n on read
    content = "Unix\nWindows\r\nMac\rMixed\n"
    file.write_text(content, newline="")

    result = await read_file_content(file)

    # Verify content is preserved
    assert "Unix" in result
    assert "Windows" in result
    assert "Mac" in result
