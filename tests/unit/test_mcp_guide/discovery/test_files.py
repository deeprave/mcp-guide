"""Tests for file discovery utilities."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_guide.discovery.files import FileInfo, discover_document_files


def test_fileinfo_has_category_field():
    """Test that FileInfo has category field."""
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


def test_fileinfo_source_defaults_to_file():
    """Test that source defaults to 'file'."""
    fi = FileInfo(path=Path("test.md"), size=0, content_size=0, mtime=datetime.now(), name="test.md")
    assert fi.source == "file"


def test_fileinfo_source_can_be_set():
    """Test that source can be set to a custom value."""
    fi = FileInfo(path=Path("test.md"), size=0, content_size=0, mtime=datetime.now(), name="test.md", source="store")
    assert fi.source == "store"


@pytest.mark.anyio
async def test_content_loader_called_on_get_content():
    """Test that content_loader is called when getting content."""

    async def loader() -> str | None:
        return "loaded content"

    fi = FileInfo(
        path=Path("test.md"), size=0, content_size=0, mtime=datetime.now(), name="test.md", content_loader=loader
    )
    result = await fi.get_content()
    assert result == "loaded content"
    assert fi.size == len("loaded content")


@pytest.mark.anyio
async def test_content_loader_returning_none():
    """Test that content_loader returning None is handled."""

    async def loader() -> str | None:
        return None

    fi = FileInfo(
        path=Path("test.md"), size=0, content_size=0, mtime=datetime.now(), name="test.md", content_loader=loader
    )
    result = await fi.get_content()
    assert result is None


@pytest.mark.anyio
async def test_content_loader_error_propagates():
    """Test that content_loader errors propagate directly."""

    async def loader() -> str | None:
        raise RuntimeError("store unavailable")

    fi = FileInfo(
        path=Path("test.md"), size=0, content_size=0, mtime=datetime.now(), name="test.md", content_loader=loader
    )
    with pytest.raises(RuntimeError, match="store unavailable"):
        await fi.get_content()


@pytest.mark.anyio
async def test_no_content_loader_falls_back_to_filesystem(tmp_path):
    """Test that without content_loader, filesystem read is used."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# From disk")

    fi = FileInfo(path=test_file, size=0, content_size=0, mtime=datetime.now(), name="test.md")
    result = await fi.get_content()
    assert result == "# From disk"


@pytest.mark.anyio
async def test_filesystem_load_error_cleared_on_retry(tmp_path):
    """Test that _load_error is cleared when a retry succeeds after initial failure."""
    test_file = tmp_path / "test.md"

    fi = FileInfo(path=test_file, size=0, content_size=0, mtime=datetime.now(), name="test.md")
    # First call fails — file doesn't exist
    with pytest.raises(OSError):
        await fi.get_content()

    # Create the file and reset state so retry is attempted
    test_file.write_text("# Retry success")
    fi._content = None
    fi._content_explicitly_set = False

    result = await fi.get_content()
    assert result == "# Retry success"


@pytest.mark.anyio
async def test_content_loader_takes_precedence_over_filesystem(tmp_path):
    """Test that content_loader is preferred over filesystem when both are available."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# From disk")

    async def loader() -> str | None:
        return "# From loader"

    fi = FileInfo(
        path=test_file,
        size=0,
        content_size=0,
        mtime=datetime.now(),
        name="test.md",
        content_loader=loader,
    )
    result = await fi.get_content()
    assert result == "# From loader"


@pytest.mark.anyio
async def test_directory_not_found():
    """Test that missing directory raises FileNotFoundError."""
    non_existent = Path("/non/existent/directory")
    with pytest.raises(FileNotFoundError):
        await discover_document_files(non_existent, ["*.txt"])


@pytest.mark.anyio
async def test_relative_path_raises_error():
    """Test that relative path raises ValueError."""
    relative_path = Path("relative/path")
    with pytest.raises(ValueError, match="must be absolute"):
        await discover_document_files(relative_path, ["*.txt"])


@pytest.mark.anyio
async def test_template_extension_patterns_raise_error(tmp_path):
    """Test that patterns with template extensions raise ValueError."""
    template_extensions = [".mustache", ".hbs", ".handlebars", ".chevron"]

    for ext in template_extensions:
        with pytest.raises(ValueError, match="should not include template extensions"):
            await discover_document_files(tmp_path, [f"*.md{ext}"])


@pytest.mark.anyio
async def test_no_matches_returns_empty_list(tmp_path):
    """Test that no matches returns empty list."""
    result = await discover_document_files(tmp_path, ["*.txt"])
    assert result == []


@pytest.mark.anyio
async def test_discover_single_file(tmp_path):
    """Test discovering a single file."""
    (tmp_path / "test.md").write_text("# Test")

    result = await discover_document_files(tmp_path, ["*.md"])

    assert len(result) == 1
    assert result[0].path == Path("test.md")
    assert result[0].name == "test.md"
    assert result[0].size > 0


@pytest.mark.anyio
async def test_discover_multiple_files(tmp_path):
    """Test discovering multiple files."""
    (tmp_path / "file1.md").write_text("# File 1")
    (tmp_path / "file2.md").write_text("# File 2")

    result = await discover_document_files(tmp_path, ["*.md"])

    assert len(result) == 2
    paths = {f.path for f in result}
    assert Path("file1.md") in paths
    assert Path("file2.md") in paths


@pytest.mark.anyio
async def test_multiple_patterns(tmp_path):
    """Test multiple patterns."""
    (tmp_path / "doc.md").write_text("# Doc")
    (tmp_path / "data.yaml").write_text("key: value")

    result = await discover_document_files(tmp_path, ["*.md", "*.yaml"])

    assert len(result) == 2
    paths = {f.path for f in result}
    assert Path("doc.md") in paths
    assert Path("data.yaml") in paths


@pytest.mark.anyio
async def test_discover_in_subdirectories(tmp_path):
    """Test discovering files in subdirectories."""
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "nested.md").write_text("# Nested")

    result = await discover_document_files(tmp_path, ["**/*.md"])

    assert len(result) == 1
    assert result[0].path == Path("sub/nested.md")


@pytest.mark.anyio
async def test_discover_template_file(tmp_path):
    """Test discovering template file."""
    (tmp_path / "doc.md.mustache").write_text("# Template")

    result = await discover_document_files(tmp_path, ["*.md"])

    assert len(result) == 1
    assert result[0].path == Path("doc.md.mustache")
    assert result[0].name == "doc.md"


@pytest.mark.anyio
async def test_prefer_non_template_over_template(tmp_path):
    """Test that non-template is preferred when both exist."""
    (tmp_path / "doc.md").write_text("# Real")
    (tmp_path / "doc.md.mustache").write_text("# Template")

    result = await discover_document_files(tmp_path, ["*.md"])

    assert len(result) == 1
    assert result[0].path == Path("doc.md")
    assert result[0].name == "doc.md"


@pytest.mark.anyio
async def test_template_replacement_when_both_exist(tmp_path):
    """Test template is excluded when non-template exists."""
    (tmp_path / "file.txt").write_text("Real")
    (tmp_path / "file.txt.mustache").write_text("Template")

    result = await discover_document_files(tmp_path, ["*.txt"])

    assert len(result) == 1
    assert result[0].path == Path("file.txt")


@pytest.mark.anyio
async def test_relative_paths(tmp_path):
    """Test paths are relative to category_dir."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file.txt").write_text("content")

    result = await discover_document_files(tmp_path, ["**/*.txt"])

    assert len(result) == 1
    assert result[0].path == Path("subdir/file.txt")
    assert not result[0].path.is_absolute()


@pytest.mark.anyio
async def test_empty_patterns_returns_empty(tmp_path):
    """Test empty patterns list returns empty results."""
    (tmp_path / "file.txt").write_text("content")

    result = await discover_document_files(tmp_path, [])

    assert result == []


@pytest.mark.anyio
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
    result = await discover_document_files(tmp_path, ["**/*.py"])

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


@pytest.mark.anyio
async def test_same_filename_different_directories(tmp_path):
    """Test that files with same name in different directories are both returned."""
    subdir1 = tmp_path / "subdir1"
    subdir2 = tmp_path / "subdir2"
    subdir1.mkdir()
    subdir2.mkdir()

    (subdir1 / "doc.md").write_text("# Doc 1")
    (subdir2 / "doc.md").write_text("# Doc 2")

    result = await discover_document_files(tmp_path, ["**/*.md"])

    # Should return BOTH files, not just one
    assert len(result) == 2
    paths = {r.path for r in result}
    assert paths == {Path("subdir1/doc.md"), Path("subdir2/doc.md")}
    # Each should have their relative path as name
    names = [r.name for r in result]
    assert "subdir1/doc.md" in names
    assert "subdir2/doc.md" in names


@pytest.mark.anyio
async def test_template_deduplication_in_subdirectory(tmp_path):
    """Test that template deduplication works correctly in subdirectories."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    # Both template and non-template in subdirectory
    (subdir / "doc.md").write_text("# Real")
    (subdir / "doc.md.mustache").write_text("# Template")

    result = await discover_document_files(tmp_path, ["**/*.md"])

    # Should only return non-template version
    assert len(result) == 1
    assert result[0].path == Path("subdir/doc.md")
    assert result[0].name == "subdir/doc.md"


@pytest.mark.anyio
async def test_template_preference_different_directories(tmp_path):
    """Test template preference is per-directory, not global."""
    # Create template in one dir, non-template in another
    (tmp_path / "subdir1").mkdir()
    (tmp_path / "subdir2").mkdir()
    (tmp_path / "subdir1" / "doc.md").write_text("real")
    (tmp_path / "subdir2" / "doc.md.mustache").write_text("template")

    result = await discover_document_files(tmp_path, ["**/*.md"])

    # Should return both files (they're in different directories)
    assert len(result) == 2
    paths = {r.path for r in result}
    assert paths == {Path("subdir1/doc.md"), Path("subdir2/doc.md.mustache")}


# --- Tests for discover_document_stored ---


@pytest.mark.anyio
async def test_discover_document_stored_returns_matching_records():
    """Test that stored documents matching patterns are returned as FileInfo."""
    from unittest.mock import AsyncMock, patch

    from mcp_guide.discovery.files import discover_document_stored
    from mcp_guide.store.document_store import DocumentRecord

    records = [
        DocumentRecord(
            id=1,
            category="docs",
            name="guide.md",
            source="http://example.com",
            source_type="url",
            metadata={},
            created_at="2025-01-01T00:00:00",
            updated_at="2025-06-01T00:00:00",
        ),
        DocumentRecord(
            id=2,
            category="docs",
            name="notes.txt",
            source="manual",
            source_type="text",
            metadata={},
            created_at="2025-01-01T00:00:00",
            updated_at="2025-06-01T00:00:00",
        ),
    ]
    with patch("mcp_guide.discovery.files.list_documents", new=AsyncMock(return_value=records)):
        result = await discover_document_stored("docs", ["*.md"])

    assert len(result) == 1
    assert result[0].name == "guide.md"
    assert result[0].source == "store"
    assert result[0].path == Path("guide.md")


@pytest.mark.anyio
async def test_discover_document_stored_case_insensitive():
    """Test that stored document matching is case-insensitive."""
    from unittest.mock import AsyncMock, patch

    from mcp_guide.discovery.files import discover_document_stored
    from mcp_guide.store.document_store import DocumentRecord

    records = [
        DocumentRecord(
            id=1,
            category="docs",
            name="README.md",
            source="x",
            source_type="url",
            metadata={},
            created_at="2025-01-01T00:00:00",
            updated_at="2025-06-01T00:00:00",
        ),
    ]
    with patch("mcp_guide.discovery.files.list_documents", new=AsyncMock(return_value=records)):
        result = await discover_document_stored("docs", ["*.md"])

    assert len(result) == 1
    assert result[0].name == "README.md"


@pytest.mark.anyio
async def test_discover_document_stored_bare_name_matches_with_extension():
    """Test that a bare pattern like 'readme' matches 'readme.md'."""
    from unittest.mock import AsyncMock, patch

    from mcp_guide.discovery.files import discover_document_stored
    from mcp_guide.store.document_store import DocumentRecord

    records = [
        DocumentRecord(
            id=1,
            category="docs",
            name="readme.md",
            source="x",
            source_type="url",
            metadata={},
            created_at="2025-01-01T00:00:00",
            updated_at="2025-06-01T00:00:00",
        ),
        DocumentRecord(
            id=2,
            category="docs",
            name="readme",
            source="x",
            source_type="text",
            metadata={},
            created_at="2025-01-01T00:00:00",
            updated_at="2025-06-01T00:00:00",
        ),
    ]
    with patch("mcp_guide.discovery.files.list_documents", new=AsyncMock(return_value=records)):
        result = await discover_document_stored("docs", ["readme"])

    assert len(result) == 2
    names = {r.name for r in result}
    assert names == {"readme.md", "readme"}


@pytest.mark.anyio
async def test_discover_document_stored_empty_when_no_match():
    """Test that no results returned when patterns don't match."""
    from unittest.mock import AsyncMock, patch

    from mcp_guide.discovery.files import discover_document_stored
    from mcp_guide.store.document_store import DocumentRecord

    records = [
        DocumentRecord(
            id=1,
            category="docs",
            name="guide.md",
            source="x",
            source_type="url",
            metadata={},
            created_at="2025-01-01T00:00:00",
            updated_at="2025-06-01T00:00:00",
        ),
    ]
    with patch("mcp_guide.discovery.files.list_documents", new=AsyncMock(return_value=records)):
        result = await discover_document_stored("docs", ["*.yaml"])

    assert result == []


@pytest.mark.anyio
async def test_discover_document_stored_has_content_loader():
    """Test that returned FileInfo has a working content_loader."""
    from unittest.mock import AsyncMock, patch

    from mcp_guide.discovery.files import discover_document_stored
    from mcp_guide.store.document_store import DocumentRecord

    records = [
        DocumentRecord(
            id=1,
            category="docs",
            name="guide.md",
            source="x",
            source_type="url",
            metadata={},
            created_at="2025-01-01T00:00:00",
            updated_at="2025-06-01T00:00:00",
        ),
    ]
    with (
        patch("mcp_guide.discovery.files.list_documents", new=AsyncMock(return_value=records)),
        patch("mcp_guide.discovery.files.get_document_content", new=AsyncMock(return_value="# Guide")) as mock_get,
    ):
        result = await discover_document_stored("docs", ["*.md"])
        content = await result[0].get_content()

    assert content == "# Guide"
    mock_get.assert_called_once_with("docs", "guide.md")


# --- Tests for merged discover_documents ---


@pytest.mark.anyio
async def test_discover_documents_without_category(tmp_path):
    """Test that discover_documents without category only returns filesystem files."""
    from mcp_guide.discovery.files import discover_documents

    (tmp_path / "readme.md").write_text("# Hello")
    result = await discover_documents(tmp_path, ["*.md"])

    assert len(result) == 1
    assert result[0].name == "readme.md"
    assert result[0].source == "file"


@pytest.mark.anyio
async def test_discover_documents_with_category_combines_sources(tmp_path):
    """Test that discover_documents with category returns both filesystem and stored."""
    from unittest.mock import AsyncMock, patch

    from mcp_guide.discovery.files import discover_documents
    from mcp_guide.store.document_store import DocumentRecord

    (tmp_path / "local.md").write_text("# Local")
    records = [
        DocumentRecord(
            id=1,
            category="docs",
            name="remote.md",
            source="x",
            source_type="url",
            metadata={},
            created_at="2025-01-01T00:00:00",
            updated_at="2025-06-01T00:00:00",
        ),
    ]
    with patch("mcp_guide.discovery.files.list_documents", new=AsyncMock(return_value=records)):
        result = await discover_documents(tmp_path, ["*.md"], category="docs")

    assert len(result) == 2
    sources = {fi.source for fi in result}
    assert sources == {"file", "store"}
