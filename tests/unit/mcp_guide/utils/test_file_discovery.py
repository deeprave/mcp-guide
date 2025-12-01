"""Tests for file discovery functionality."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_guide.utils.file_discovery import (
    TEMPLATE_EXTENSION,
    FileInfo,
    discover_category_files,
)


@pytest.fixture
def temp_category_dir(tmp_path):
    """Create a temporary category directory."""
    category_dir = tmp_path / "category"
    category_dir.mkdir()
    return category_dir


def test_fileinfo_dataclass():
    """Test FileInfo dataclass creation."""
    path = Path("test.txt")
    size = 1024
    mtime = datetime.now()
    basename = "test.txt"

    file_info = FileInfo(path=path, size=size, mtime=mtime, basename=basename)

    assert file_info.path == path
    assert file_info.size == size
    assert file_info.mtime == mtime
    assert file_info.basename == basename


@pytest.mark.asyncio
async def test_directory_not_found():
    """Test that missing directory raises FileNotFoundError."""
    non_existent = Path("/non/existent/directory")

    with pytest.raises(FileNotFoundError):
        await discover_category_files(non_existent, ["*.txt"])


@pytest.mark.asyncio
async def test_relative_path_raises_error():
    """Test that relative path raises ValueError."""
    relative_path = Path("relative/path")

    with pytest.raises(ValueError, match="must be absolute"):
        await discover_category_files(relative_path, ["*.txt"])


@pytest.mark.asyncio
async def test_mustache_pattern_raises_error(temp_category_dir):
    """Test that patterns ending with template extension are rejected."""
    with pytest.raises(ValueError, match=f"Patterns should not include {TEMPLATE_EXTENSION} extension"):
        await discover_category_files(temp_category_dir, [f"*.md{TEMPLATE_EXTENSION}"])


@pytest.mark.asyncio
async def test_no_matches_returns_empty_list(temp_category_dir):
    """Test that no matching files returns empty list."""
    result = await discover_category_files(temp_category_dir, ["*.txt"])

    assert result == []


@pytest.mark.asyncio
async def test_discover_single_file(temp_category_dir):
    """Test discovering a single file with metadata."""
    test_file = temp_category_dir / "test.txt"
    test_file.write_text("hello world")

    result = await discover_category_files(temp_category_dir, ["*.txt"])

    assert len(result) == 1
    assert result[0].path == Path("test.txt")
    assert result[0].size == 11
    assert isinstance(result[0].mtime, datetime)
    assert result[0].basename == "test.txt"


@pytest.mark.asyncio
async def test_discover_multiple_files(temp_category_dir):
    """Test discovering multiple files."""
    (temp_category_dir / "file1.md").write_text("content1")
    (temp_category_dir / "file2.md").write_text("content2")
    (temp_category_dir / "file3.md").write_text("content3")

    result = await discover_category_files(temp_category_dir, ["*.md"])

    assert len(result) == 3
    paths = {r.path for r in result}
    assert paths == {Path("file1.md"), Path("file2.md"), Path("file3.md")}
    for file_info in result:
        assert file_info.size > 0
        assert isinstance(file_info.mtime, datetime)


@pytest.mark.asyncio
async def test_multiple_patterns(temp_category_dir):
    """Test multiple glob patterns."""
    (temp_category_dir / "file.txt").write_text("text")
    (temp_category_dir / "file.md").write_text("markdown")
    (temp_category_dir / "file.py").write_text("python")

    result = await discover_category_files(temp_category_dir, ["*.txt", "*.md"])

    assert len(result) == 2
    paths = {r.path for r in result}
    assert paths == {Path("file.txt"), Path("file.md")}


@pytest.mark.asyncio
async def test_relative_paths(temp_category_dir):
    """Test paths are relative to category_dir."""
    subdir = temp_category_dir / "subdir"
    subdir.mkdir()
    (subdir / "file.txt").write_text("content")

    result = await discover_category_files(temp_category_dir, ["**/*.txt"])

    assert len(result) == 1
    assert result[0].path == Path("subdir/file.txt")
    assert not result[0].path.is_absolute()


@pytest.mark.asyncio
async def test_discover_in_subdirectories(temp_category_dir):
    """Test recursive pattern finds nested files."""
    deep_dir = temp_category_dir / "a" / "b"
    deep_dir.mkdir(parents=True)
    (deep_dir / "file.txt").write_text("nested")

    result = await discover_category_files(temp_category_dir, ["**/*.txt"])

    assert len(result) == 1
    assert result[0].path == Path("a/b/file.txt")


@pytest.mark.asyncio
async def test_empty_patterns_returns_empty(temp_category_dir):
    """Test empty patterns list returns empty results."""
    (temp_category_dir / "file.txt").write_text("content")

    result = await discover_category_files(temp_category_dir, [])

    assert result == []


@pytest.mark.asyncio
async def test_integration_realistic_category(temp_category_dir):
    """Test realistic category structure with multiple file types and subdirectories."""
    # Create structure
    (temp_category_dir / "README.md").write_text("# Documentation")
    (temp_category_dir / "config.json").write_text("{}")

    src_dir = temp_category_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('hello')")
    (src_dir / "utils.py").write_text("def helper(): pass")

    tests_dir = temp_category_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("def test(): pass")

    # Search for Python files
    result = await discover_category_files(temp_category_dir, ["**/*.py"])

    assert len(result) == 3
    paths = {r.path for r in result}
    assert paths == {
        Path("src/main.py"),
        Path("src/utils.py"),
        Path("tests/test_main.py"),
    }

    # Verify all have metadata
    for file_info in result:
        assert file_info.size > 0
        assert isinstance(file_info.mtime, datetime)
        assert not file_info.path.is_absolute()


@pytest.mark.asyncio
async def test_discover_template_file(temp_category_dir):
    """Test discovering .mustache template files."""
    (temp_category_dir / "doc.md.mustache").write_text("# {{title}}")

    result = await discover_category_files(temp_category_dir, ["*.md"])

    assert len(result) == 1
    assert result[0].path == Path("doc.md.mustache")
    assert result[0].basename == "doc.md"
    assert result[0].size > 0


@pytest.mark.asyncio
async def test_template_basename_strips_mustache(temp_category_dir):
    """Test that basename strips .mustache extension."""
    (temp_category_dir / "config.json.mustache").write_text("{}")
    (temp_category_dir / "readme.txt.mustache").write_text("text")

    result = await discover_category_files(temp_category_dir, ["*.json", "*.txt"])

    assert len(result) == 2
    basenames = {r.basename for r in result}
    assert basenames == {"config.json", "readme.txt"}


@pytest.mark.asyncio
async def test_pattern_finds_both_regular_and_template(temp_category_dir):
    """Test that pattern *.md finds both .md and .md.mustache files."""
    (temp_category_dir / "doc.md.mustache").write_text("# Template")
    (temp_category_dir / "other.txt").write_text("text")

    result = await discover_category_files(temp_category_dir, ["*.md"])

    assert len(result) == 1
    assert result[0].path == Path("doc.md.mustache")
    assert result[0].basename == "doc.md"


@pytest.mark.asyncio
async def test_prefer_non_template_over_template(temp_category_dir):
    """Test that non-template is preferred when both exist."""
    (temp_category_dir / "doc.md").write_text("# Real")
    (temp_category_dir / "doc.md.mustache").write_text("# Template")

    result = await discover_category_files(temp_category_dir, ["*.md"])

    # Should only return the non-template version
    assert len(result) == 1
    assert result[0].path == Path("doc.md")
    assert result[0].basename == "doc.md"


@pytest.mark.asyncio
async def test_same_filename_different_directories(temp_category_dir):
    """Test that files with same name in different directories are both returned."""
    subdir1 = temp_category_dir / "subdir1"
    subdir2 = temp_category_dir / "subdir2"
    subdir1.mkdir()
    subdir2.mkdir()

    (subdir1 / "doc.md").write_text("# Doc 1")
    (subdir2 / "doc.md").write_text("# Doc 2")

    result = await discover_category_files(temp_category_dir, ["**/*.md"])

    # Should return BOTH files, not just one
    assert len(result) == 2
    paths = {r.path for r in result}
    assert paths == {Path("subdir1/doc.md"), Path("subdir2/doc.md")}
    # Both should have same basename
    assert all(r.basename == "doc.md" for r in result)


@pytest.mark.asyncio
async def test_template_deduplication_in_subdirectory(temp_category_dir):
    """Test that template deduplication works correctly in subdirectories."""
    subdir = temp_category_dir / "subdir"
    subdir.mkdir()

    # Both template and non-template in subdirectory
    (subdir / "doc.md").write_text("# Real")
    (subdir / "doc.md.mustache").write_text("# Template")

    result = await discover_category_files(temp_category_dir, ["**/*.md"])

    # Should only return non-template version
    assert len(result) == 1
    assert result[0].path == Path("subdir/doc.md")
    assert result[0].basename == "doc.md"


@pytest.mark.asyncio
async def test_template_preference_different_directories(temp_category_dir):
    """Test template preference is per-directory, not global."""
    # Create template in one dir, non-template in another
    (temp_category_dir / "subdir1").mkdir()
    (temp_category_dir / "subdir2").mkdir()
    (temp_category_dir / "subdir1" / "doc.md").write_text("real")
    (temp_category_dir / "subdir2" / "doc.md.mustache").write_text("template")

    result = await discover_category_files(temp_category_dir, ["**/*.md"])

    # Should return both files (they're in different directories)
    assert len(result) == 2
    paths = {r.path for r in result}
    assert paths == {Path("subdir1/doc.md"), Path("subdir2/doc.md.mustache")}


@pytest.mark.asyncio
async def test_template_replacement_when_both_exist(temp_category_dir):
    """Test that non-template replaces template when both exist."""
    # The pattern expansion creates ["*.md", "*.md.mustache"]
    # safe_glob_search processes these and may return results in any order
    # This test verifies the deduplication logic handles both orders correctly
    (temp_category_dir / "doc.md.mustache").write_text("# Template")
    (temp_category_dir / "doc.md").write_text("# Real")

    result = await discover_category_files(temp_category_dir, ["*.md"])

    # Should always return non-template
    assert len(result) == 1
    assert result[0].path == Path("doc.md")
    assert result[0].basename == "doc.md"
