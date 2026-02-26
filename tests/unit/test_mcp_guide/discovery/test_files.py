"""Tests for file discovery utilities."""

from pathlib import Path

import pytest

from mcp_guide.discovery.files import FileInfo, discover_category_files


def test_fileinfo_has_category_field():
    """Test that FileInfo has category field."""
    from datetime import datetime

    file_info = FileInfo(
        path=Path("test.md"),
        size=100,
        content_size=100,
        mtime=datetime.now(),
        name="test.md",
    )
    assert hasattr(file_info, "category")
    assert file_info.category is None


def test_fileinfo_category_can_be_set():
    """Test that category field can be set."""
    from datetime import datetime

    from mcp_guide.models.project import Category

    category = Category(dir="docs/", patterns=["README"], name="docs")
    file_info = FileInfo(
        path=Path("test.md"),
        size=100,
        content_size=100,
        mtime=datetime.now(),
        name="test.md",
        category=category,
    )
    assert file_info.category == category
    assert file_info.category.name == "docs"


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
async def test_template_extension_patterns_raise_error(tmp_path):
    """Test that patterns with template extensions raise ValueError."""
    template_extensions = [".mustache", ".hbs", ".handlebars", ".chevron"]

    for ext in template_extensions:
        with pytest.raises(ValueError, match="should not include template extensions"):
            await discover_category_files(tmp_path, [f"*.md{ext}"])


@pytest.mark.asyncio
async def test_no_matches_returns_empty_list(tmp_path):
    """Test that no matches returns empty list."""
    result = await discover_category_files(tmp_path, ["*.txt"])
    assert result == []


@pytest.mark.asyncio
async def test_discover_single_file(tmp_path):
    """Test discovering a single file."""
    (tmp_path / "test.md").write_text("# Test")

    result = await discover_category_files(tmp_path, ["*.md"])

    assert len(result) == 1
    assert result[0].path == Path("test.md")
    assert result[0].name == "test.md"
    assert result[0].size > 0


@pytest.mark.asyncio
async def test_discover_multiple_files(tmp_path):
    """Test discovering multiple files."""
    (tmp_path / "file1.md").write_text("# File 1")
    (tmp_path / "file2.md").write_text("# File 2")

    result = await discover_category_files(tmp_path, ["*.md"])

    assert len(result) == 2
    paths = {f.path for f in result}
    assert Path("file1.md") in paths
    assert Path("file2.md") in paths


@pytest.mark.asyncio
async def test_multiple_patterns(tmp_path):
    """Test multiple patterns."""
    (tmp_path / "doc.md").write_text("# Doc")
    (tmp_path / "data.yaml").write_text("key: value")

    result = await discover_category_files(tmp_path, ["*.md", "*.yaml"])

    assert len(result) == 2
    paths = {f.path for f in result}
    assert Path("doc.md") in paths
    assert Path("data.yaml") in paths


@pytest.mark.asyncio
async def test_discover_in_subdirectories(tmp_path):
    """Test discovering files in subdirectories."""
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "nested.md").write_text("# Nested")

    result = await discover_category_files(tmp_path, ["**/*.md"])

    assert len(result) == 1
    assert result[0].path == Path("sub/nested.md")


@pytest.mark.asyncio
async def test_discover_template_file(tmp_path):
    """Test discovering template file."""
    (tmp_path / "doc.md.mustache").write_text("# Template")

    result = await discover_category_files(tmp_path, ["*.md"])

    assert len(result) == 1
    assert result[0].path == Path("doc.md.mustache")
    assert result[0].name == "doc.md"


@pytest.mark.asyncio
async def test_prefer_non_template_over_template(tmp_path):
    """Test that non-template is preferred when both exist."""
    (tmp_path / "doc.md").write_text("# Real")
    (tmp_path / "doc.md.mustache").write_text("# Template")

    result = await discover_category_files(tmp_path, ["*.md"])

    assert len(result) == 1
    assert result[0].path == Path("doc.md")
    assert result[0].name == "doc.md"


@pytest.mark.asyncio
async def test_template_replacement_when_both_exist(tmp_path):
    """Test template is excluded when non-template exists."""
    (tmp_path / "file.txt").write_text("Real")
    (tmp_path / "file.txt.mustache").write_text("Template")

    result = await discover_category_files(tmp_path, ["*.txt"])

    assert len(result) == 1
    assert result[0].path == Path("file.txt")


@pytest.mark.asyncio
async def test_relative_paths(tmp_path):
    """Test paths are relative to category_dir."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file.txt").write_text("content")

    result = await discover_category_files(tmp_path, ["**/*.txt"])

    assert len(result) == 1
    assert result[0].path == Path("subdir/file.txt")
    assert not result[0].path.is_absolute()


@pytest.mark.asyncio
async def test_empty_patterns_returns_empty(tmp_path):
    """Test empty patterns list returns empty results."""
    (tmp_path / "file.txt").write_text("content")

    result = await discover_category_files(tmp_path, [])

    assert result == []


@pytest.mark.asyncio
async def test_integration_realistic_category(tmp_path):
    """Test realistic category structure with multiple file types and subdirectories."""
    from datetime import datetime

    # Create structure
    (tmp_path / "README.md").write_text("# Documentation")
    (tmp_path / "config.json").write_text("{}")

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('hello')")
    (src_dir / "utils.py").write_text("def helper(): pass")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("def test(): pass")

    # Search for Python files
    result = await discover_category_files(tmp_path, ["**/*.py"])

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
async def test_same_filename_different_directories(tmp_path):
    """Test that files with same name in different directories are both returned."""
    subdir1 = tmp_path / "subdir1"
    subdir2 = tmp_path / "subdir2"
    subdir1.mkdir()
    subdir2.mkdir()

    (subdir1 / "doc.md").write_text("# Doc 1")
    (subdir2 / "doc.md").write_text("# Doc 2")

    result = await discover_category_files(tmp_path, ["**/*.md"])

    # Should return BOTH files, not just one
    assert len(result) == 2
    paths = {r.path for r in result}
    assert paths == {Path("subdir1/doc.md"), Path("subdir2/doc.md")}
    # Each should have their relative path as name
    names = [r.name for r in result]
    assert "subdir1/doc.md" in names
    assert "subdir2/doc.md" in names


@pytest.mark.asyncio
async def test_template_deduplication_in_subdirectory(tmp_path):
    """Test that template deduplication works correctly in subdirectories."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    # Both template and non-template in subdirectory
    (subdir / "doc.md").write_text("# Real")
    (subdir / "doc.md.mustache").write_text("# Template")

    result = await discover_category_files(tmp_path, ["**/*.md"])

    # Should only return non-template version
    assert len(result) == 1
    assert result[0].path == Path("subdir/doc.md")
    assert result[0].name == "subdir/doc.md"


@pytest.mark.asyncio
async def test_template_preference_different_directories(tmp_path):
    """Test template preference is per-directory, not global."""
    # Create template in one dir, non-template in another
    (tmp_path / "subdir1").mkdir()
    (tmp_path / "subdir2").mkdir()
    (tmp_path / "subdir1" / "doc.md").write_text("real")
    (tmp_path / "subdir2" / "doc.md.mustache").write_text("template")

    result = await discover_category_files(tmp_path, ["**/*.md"])

    # Should return both files (they're in different directories)
    assert len(result) == 2
    paths = {r.path for r in result}
    assert paths == {Path("subdir1/doc.md"), Path("subdir2/doc.md.mustache")}
