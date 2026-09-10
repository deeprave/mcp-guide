"""Tests for file discovery utilities."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_guide.discovery.files import FileInfo, discover_document_files


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
async def test_filesystem_load_error_cleared_on_retry(tmp_path):
    """Test that _load_error is cleared when a retry succeeds after initial failure."""
    test_file = tmp_path / "test.md"

    fi = FileInfo(path=test_file, size=0, content_size=0, mtime=datetime.now(), name="test.md")
    # First call fails — file doesn't exist
    with pytest.raises(OSError):
        await fi.get_content()

    # Creating the missing file is sufficient for a public retry.
    test_file.write_text("# Retry success")

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
    assert fi.size == len("# From loader")


@pytest.mark.anyio
async def test_directory_not_found():
    """Test that missing directory raises FileNotFoundError."""
    non_existent = Path("/non/existent/directory")
    with pytest.raises(FileNotFoundError):
        await discover_document_files(non_existent, ["*.txt"])


@pytest.mark.anyio
async def test_relative_base_dir_is_resolved_against_cwd(tmp_path, monkeypatch):
    """A relative configured path is resolved at use time, not rejected."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "note.md").write_text("hello\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    found = await discover_document_files(Path("docs"), ["*.md"])
    assert [info.path.name for info in found] == ["note.md"]


@pytest.mark.anyio
async def test_tilde_base_dir_is_resolved_before_the_absolute_check(tmp_path, monkeypatch):
    """A configured ``~/...`` path is host-absolute after LazyPath.resolve()."""
    home = tmp_path / "home"
    commands = home / "docs" / "_commands"
    commands.mkdir(parents=True)
    (commands / "help.mustache").write_text("hello\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))

    found = await discover_document_files(Path("~/docs/../docs/_commands"), ["help"])
    assert [info.path.name for info in found] == ["help.mustache"]


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
        stat = (tmp_path / file_info.path).stat()
        assert file_info.size == stat.st_size
        assert file_info.name == file_info.path.as_posix()
        assert file_info.mtime == datetime.fromtimestamp(stat.st_mtime)
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


# --- Tests for read_raw ---


@pytest.mark.anyio
async def test_read_raw_with_content_loader():
    """Test read_raw returns content from content_loader."""

    async def loader() -> str | None:
        return "raw loaded content"

    fi = FileInfo(
        path=Path("test.md"), size=0, content_size=0, mtime=datetime.now(), name="test.md", content_loader=loader
    )
    result = await fi.read_raw()
    assert result == "raw loaded content"


@pytest.mark.anyio
async def test_read_raw_loader_returns_none_raises():
    """Test read_raw raises FileNotFoundError when loader returns None."""

    async def loader() -> str | None:
        return None

    fi = FileInfo(
        path=Path("test.md"), size=0, content_size=0, mtime=datetime.now(), name="test.md", content_loader=loader
    )
    with pytest.raises(FileNotFoundError, match="No content available"):
        await fi.read_raw()


@pytest.mark.anyio
async def test_read_raw_loader_error_propagates():
    """Test read_raw propagates content_loader exceptions."""

    async def loader() -> str | None:
        raise RuntimeError("store unavailable")

    fi = FileInfo(
        path=Path("test.md"), size=0, content_size=0, mtime=datetime.now(), name="test.md", content_loader=loader
    )
    with pytest.raises(RuntimeError, match="store unavailable"):
        await fi.read_raw()


@pytest.mark.anyio
async def test_read_raw_falls_back_to_filesystem(tmp_path):
    """Test read_raw reads from filesystem when no content_loader."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# From disk")

    fi = FileInfo(path=test_file, size=0, content_size=0, mtime=datetime.now(), name="test.md")
    result = await fi.read_raw()
    assert result == "# From disk"


@pytest.mark.anyio
async def test_read_raw_filesystem_missing_raises():
    """Test read_raw raises when filesystem file doesn't exist."""
    fi = FileInfo(path=Path("/nonexistent/file.md"), size=0, content_size=0, mtime=datetime.now(), name="file.md")
    with pytest.raises(FileNotFoundError):
        await fi.read_raw()


@pytest.mark.anyio
async def test_stored_discovery_filters_loads_and_combines_real_sources(tmp_path, monkeypatch):
    from mcp_guide.discovery.files import discover_document_stored, discover_documents
    from mcp_guide.store.document_store import add_document

    monkeypatch.setattr("mcp_guide.store.document_store.get_documents_db", lambda: tmp_path / "documents.db")
    for name in ("readme", "readme.md", "readme.md.mustache", "notes.txt"):
        await add_document("docs", name, "https://example.test", "url", "# Stored " + name, metadata={"title": name})
    (tmp_path / "local.md").write_text("# Local")
    bare = await discover_document_stored("docs", ["readme"])
    assert {item.name for item in bare} == {"readme", "readme.md", "readme.md.mustache"}
    assert await discover_document_stored("docs", ["*.yaml"]) == []
    matched = await discover_document_stored("docs", ["*.md"])
    assert {item.name for item in matched} == {"readme.md", "readme.md.mustache"}
    for item in matched:
        assert item.source == "store"
        assert item.path == Path(item.name)
        assert await item.get_content() == "# Stored " + item.name
        assert await item.read_raw() == "# Stored " + item.name
        assert await item.get_frontmatter() == {"title": item.name}
    files = await discover_documents(tmp_path, ["*.md"])
    assert [(item.name, item.source) for item in files] == [("local.md", "file")]
    combined = await discover_documents(tmp_path, ["*.md"], category="docs")
    assert {(item.name, item.source) for item in combined} == {
        ("local.md", "file"),
        ("readme.md", "store"),
        ("readme.md.mustache", "store"),
    }


def test_fileinfo_resolve_rechecks_absolute_path_containment(tmp_path) -> None:
    """An already-absolute path still goes through the resolver's containment check."""
    docroot = (tmp_path / "documents").resolve()
    inside = docroot / "guides" / "intro.md"

    def resolver(relative_path: str | Path) -> Path:
        requested = Path(relative_path)
        if requested.is_absolute():
            candidate = requested
        else:
            candidate = docroot / requested
        candidate.relative_to(docroot)
        return candidate

    relative = FileInfo(path=Path("intro.md"), size=0, content_size=0, mtime=datetime.now(), name="intro.md")
    assert relative.resolve(resolver, "guides") == inside

    already_absolute = FileInfo(path=inside, size=0, content_size=0, mtime=datetime.now(), name="intro.md")
    assert already_absolute.resolve(resolver) == inside

    escaped = FileInfo(path=tmp_path / "outside.md", size=0, content_size=0, mtime=datetime.now(), name="outside.md")
    with pytest.raises(ValueError):
        escaped.resolve(resolver)


@pytest.mark.anyio
async def test_filesystem_discovery_preserves_glob_truncation_diagnostic(tmp_path, monkeypatch):
    (tmp_path / "first.md").write_text("first")
    (tmp_path / "second.md").write_text("second")
    monkeypatch.setattr("mcp_guide.discovery.patterns.MAX_GLOB_DIRECTORY_ENTRIES", 1)

    files = await discover_document_files(tmp_path, ["**/*.md"])

    assert len(files) == 1
    assert files.truncation_reasons == {"directory entry count"}
