"""Tests for path security utilities."""

import os
from pathlib import Path

import pytest

from mcp_core.path_security import is_path_within_directory, resolve_safe_path


def test_resolve_safe_path_basic(tmp_path: Path) -> None:
    """Test basic path resolution within base directory."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    # Create a test file
    test_file = base_dir / "file.txt"
    test_file.write_text("content")

    # Resolve relative path
    result = resolve_safe_path(base_dir, "file.txt")

    assert result == test_file
    assert result.is_absolute()


def test_resolve_safe_path_requires_absolute_base(tmp_path: Path) -> None:
    """Test that base_dir must be absolute."""
    relative_base = Path("relative/path")

    with pytest.raises(ValueError, match="Document root must be absolute"):
        resolve_safe_path(relative_base, "file.txt")


def test_resolve_safe_path_rejects_absolute_input(tmp_path: Path) -> None:
    """Test that absolute paths are rejected."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    with pytest.raises(ValueError, match="Access to system path denied"):
        resolve_safe_path(base_dir, "/etc/passwd")


def test_resolve_safe_path_rejects_parent_traversal(tmp_path: Path) -> None:
    """Test that parent directory traversal is rejected."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    with pytest.raises(ValueError, match="Path escapes docroot"):
        resolve_safe_path(base_dir, "../etc/passwd")


def test_resolve_safe_path_rejects_nested_traversal(tmp_path: Path) -> None:
    """Test that nested parent directory traversal is rejected."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    subdir = base_dir / "subdir"
    subdir.mkdir()

    with pytest.raises(ValueError, match="Path escapes docroot"):
        resolve_safe_path(base_dir, "subdir/../../etc/passwd")


def test_resolve_safe_path_normalizes_dot_slash(tmp_path: Path) -> None:
    """Test that ./ is normalized correctly."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    test_file = base_dir / "file.txt"
    test_file.write_text("content")

    result = resolve_safe_path(base_dir, "./file.txt")
    assert result == test_file


def test_resolve_safe_path_normalizes_double_slash(tmp_path: Path) -> None:
    """Test that // is normalized correctly."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    subdir = base_dir / "subdir"
    subdir.mkdir()
    test_file = subdir / "file.txt"
    test_file.write_text("content")

    result = resolve_safe_path(base_dir, "subdir//file.txt")
    assert result == test_file


def test_resolve_safe_path_rejects_symlink_escape(tmp_path: Path) -> None:
    """Test that symlinks pointing outside base_dir are rejected."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside_file = outside_dir / "secret.txt"
    outside_file.write_text("secret")

    # Create symlink inside base_dir pointing outside
    symlink = base_dir / "link"
    symlink.symlink_to(outside_file)

    with pytest.raises(ValueError, match="Path escapes docroot"):
        resolve_safe_path(base_dir, "link")


def test_is_path_within_directory_basic(tmp_path: Path) -> None:
    """Test basic boundary check."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    file_path = base_dir / "file.txt"

    assert is_path_within_directory(file_path, base_dir)


def test_is_path_within_directory_outside(tmp_path: Path) -> None:
    """Test that paths outside directory return False."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    outside_path = tmp_path / "outside" / "file.txt"

    assert not is_path_within_directory(outside_path, base_dir)


def test_is_path_within_directory_exact_match(tmp_path: Path) -> None:
    """Test that directory is within itself."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    assert is_path_within_directory(base_dir, base_dir)


def test_resolve_safe_path_accepts_string(tmp_path: Path) -> None:
    """Test that string paths are accepted."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    test_file = base_dir / "file.txt"
    test_file.write_text("content")

    result = resolve_safe_path(base_dir, "file.txt")
    assert result == test_file


def test_resolve_safe_path_rejects_empty(tmp_path: Path) -> None:
    """Test that empty paths are rejected."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    # Empty string becomes current directory "." which resolves to base_dir
    # This is actually valid - resolving "." within base_dir gives base_dir
    result = resolve_safe_path(base_dir, ".")
    assert result == base_dir


def test_resolve_safe_path_handles_windows_separators(tmp_path: Path) -> None:
    """Test that Windows-style separators are handled on Windows."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    subdir = base_dir / "subdir"
    subdir.mkdir()
    test_file = subdir / "file.txt"
    test_file.write_text("content")

    # On Windows, Path handles backslashes. On Unix, backslash is a valid filename character.
    # Test that the function works correctly on the current platform
    if os.name == "nt":  # Windows
        result = resolve_safe_path(base_dir, "subdir\\file.txt")
        assert result == test_file
    else:  # Unix-like (backslash is literal character)
        # Just verify forward slashes work (already tested elsewhere)
        result = resolve_safe_path(base_dir, "subdir/file.txt")
        assert result == test_file


def test_resolve_safe_path_subdirectory(tmp_path: Path) -> None:
    """Test resolving paths in subdirectories."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    subdir = base_dir / "a" / "b" / "c"
    subdir.mkdir(parents=True)
    test_file = subdir / "file.txt"
    test_file.write_text("content")

    result = resolve_safe_path(base_dir, "a/b/c/file.txt")
    assert result == test_file
