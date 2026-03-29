"""Tests for category_list_files source filter parameter."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from mcp_guide.tools.tool_category import CategoryListFilesArgs, internal_category_list_files


def test_source_filter_accepts_files():
    """Source filter accepts 'files'."""
    args = CategoryListFilesArgs(category="docs", source="files")
    assert args.source == "files"


def test_source_filter_accepts_stored():
    """Source filter accepts 'stored'."""
    args = CategoryListFilesArgs(category="docs", source="stored")
    assert args.source == "stored"


def test_source_filter_defaults_to_none():
    """Source filter defaults to None (both sources)."""
    args = CategoryListFilesArgs(category="docs")
    assert args.source is None


def test_source_filter_rejects_invalid_value():
    """Source filter rejects invalid values."""
    with pytest.raises(ValidationError):
        CategoryListFilesArgs(category="docs", source="invalid")


def test_name_filter_defaults_to_none():
    """Name filter defaults to None."""
    args = CategoryListFilesArgs(category="docs")
    assert args.name is None


def test_name_filter_accepts_string():
    """Name filter accepts a string value."""
    args = CategoryListFilesArgs(category="docs", name="readme.md")
    assert args.name == "readme.md"


# --- Integration-style tests for name filter and enriched stored doc info ---


def _mock_session(categories):
    """Create a mock session with given categories."""
    project = SimpleNamespace(categories=categories)
    session = AsyncMock()
    session.get_project = AsyncMock(return_value=project)
    session.get_docroot = AsyncMock(return_value="/fake/docroot")
    return session


@pytest.mark.anyio
async def test_name_filter_limits_results():
    """Name filter returns only matching document."""
    cat = SimpleNamespace(dir="docs", patterns=["**/*"])
    session = _mock_session({"docs": cat})
    record_a = SimpleNamespace(
        name="a.md",
        metadata={"description": "Doc A"},
        source_type="file",
        source="/path/a.md",
        created_at="2026-01-01",
        updated_at="2026-01-02",
    )
    record_b = SimpleNamespace(
        name="b.md",
        metadata={},
        source_type="file",
        source="/path/b.md",
        created_at="2026-01-01",
        updated_at="2026-01-02",
    )

    with (
        patch("mcp_guide.tools.tool_helpers.get_session", return_value=session),
        patch("mcp_guide.tools.tool_category.list_documents", new=AsyncMock(return_value=[record_a, record_b])),
    ):
        args = CategoryListFilesArgs(category="docs", source="stored", name="a.md")
        result = await internal_category_list_files(args)
        assert result.success is True
        assert len(result.value) == 1
        assert result.value[0]["path"] == "a.md"


@pytest.mark.anyio
async def test_stored_doc_enriched_with_metadata():
    """Stored doc includes metadata, timestamps, source info."""
    cat = SimpleNamespace(dir="docs", patterns=["**/*"])
    session = _mock_session({"docs": cat})
    record = SimpleNamespace(
        name="readme.md",
        metadata={"description": "A readme", "type": "agent/information"},
        source_type="file",
        source="/path/readme.md",
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-02T00:00:00",
    )

    with (
        patch("mcp_guide.tools.tool_helpers.get_session", return_value=session),
        patch("mcp_guide.tools.tool_category.list_documents", new=AsyncMock(return_value=[record])),
    ):
        args = CategoryListFilesArgs(category="docs", source="stored")
        result = await internal_category_list_files(args)
        assert result.success is True
        info = result.value[0]
        assert info["description"] == "A readme"
        assert info["metadata"] == {"description": "A readme", "type": "agent/information"}
        assert info["source_type"] == "file"
        assert info["source_path"] == "/path/readme.md"
        assert info["created_at"] == "2026-01-01T00:00:00"
        assert info["updated_at"] == "2026-01-02T00:00:00"
