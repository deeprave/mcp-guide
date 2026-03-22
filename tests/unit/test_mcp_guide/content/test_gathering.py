"""Tests for content gathering deduplication logic."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_guide.content.gathering import gather_content
from mcp_guide.discovery.files import FileInfo
from mcp_guide.models import Category, Collection, Project


def _make_file(name: str, *, source: str = "file") -> FileInfo:
    return FileInfo(
        path=Path(name),
        size=0,
        content_size=0,
        mtime=datetime(2024, 1, 1),
        name=name,
        source=source,
        content=f"content of {name}",
    )


class _MockSession:
    def __init__(self, docroot: str):
        self._docroot = docroot

    async def get_docroot(self):
        return self._docroot


@pytest.mark.anyio
async def test_stored_and_filesystem_same_name_both_appear(tmp_path, monkeypatch):
    """Stored document and filesystem file with same name must both appear."""
    category_dir = tmp_path / "docs"
    category_dir.mkdir()
    (category_dir / "readme.md").write_text("filesystem content")

    project = Project(
        name="test",
        categories={"docs": Category(dir="docs", name="docs", patterns=["*.md"])},
    )

    stored_file = _make_file("readme.md", source="store")
    stored_file.category = project.categories["docs"]

    original_gather = gather_content.__wrapped__ if hasattr(gather_content, "__wrapped__") else None

    # Patch discover_documents to return both filesystem and stored
    async def mock_discover(category_dir, patterns, category=None):
        fs_file = _make_file("readme.md", source="file")
        return [fs_file, stored_file]

    monkeypatch.setattr("mcp_guide.content.gathering.discover_documents", mock_discover)

    session = _MockSession(str(tmp_path))
    result = await gather_content(session, project, "docs")

    assert len(result) == 2
    sources = {f.source for f in result}
    assert sources == {"file", "store"}


@pytest.mark.anyio
async def test_stored_doc_deduped_across_overlapping_collections(tmp_path, monkeypatch):
    """Same stored document appearing via two collections must be deduped."""
    category_dir = tmp_path / "docs"
    category_dir.mkdir()

    project = Project(
        name="test",
        categories={"docs": Category(dir="docs", name="docs", patterns=["*.md"])},
        collections={
            "col1": Collection(categories=["docs"]),
            "col2": Collection(categories=["docs"]),
        },
    )

    async def mock_discover(category_dir, patterns, category=None):
        stored = _make_file("notes.md", source="store")
        stored.category = project.categories["docs"]
        return [stored]

    monkeypatch.setattr("mcp_guide.content.gathering.discover_documents", mock_discover)

    session = _MockSession(str(tmp_path))
    result = await gather_content(session, project, "col1,col2")

    # Same (category, name) from two collections → only one copy
    stored_results = [f for f in result if f.source == "store"]
    assert len(stored_results) == 1
