"""Tests for file_reader module."""

from pathlib import Path

import pytest

from mcp_guide.core.file_reader import read_file_content


@pytest.mark.anyio
async def test_read_empty_file(tmp_path: Path) -> None:
    """Test reading empty file."""
    file = tmp_path / "empty.txt"
    file.touch()

    result = await read_file_content(file)

    assert result == ""


@pytest.mark.anyio
async def test_binary_file_raises_error(tmp_path: Path) -> None:
    """Test that binary files raise UnicodeDecodeError."""
    file = tmp_path / "binary.bin"
    file.write_bytes(b"\x00\x01\x02\x03\xff\xfe")

    with pytest.raises(UnicodeDecodeError):
        await read_file_content(file)


@pytest.mark.anyio
async def test_invalid_utf8_raises_error(tmp_path: Path) -> None:
    """Test that invalid UTF-8 raises UnicodeDecodeError."""
    file = tmp_path / "invalid.txt"
    # Write invalid UTF-8 sequence
    file.write_bytes(b"Valid text \xc3\x28 invalid")

    with pytest.raises(UnicodeDecodeError):
        await read_file_content(file)


@pytest.mark.anyio
async def test_permission_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that permission errors are raised in a platform-independent way."""

    async def _raise_permission_error(*args: object, **kwargs: object) -> str:
        raise PermissionError("mocked permission error")

    monkeypatch.setattr("mcp_guide.core.file_reader.AsyncPath.read_text", _raise_permission_error)

    with pytest.raises(PermissionError):
        await read_file_content(Path("noperm.txt"))


@pytest.mark.anyio
async def test_missing_file_raises_error(tmp_path: Path) -> None:
    """Test that missing files raise FileNotFoundError."""
    file = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        await read_file_content(file)


@pytest.mark.anyio
async def test_unicode_content(tmp_path: Path) -> None:
    """Test reading file with Unicode characters."""
    file = tmp_path / "unicode.txt"
    content = "Hello 世界 🌍\n  Spaces and tabs\t  \n"
    file.write_text(content)

    result = await read_file_content(file)

    assert result == content
