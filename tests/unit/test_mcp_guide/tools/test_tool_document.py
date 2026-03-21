"""Tests for document_remove tool."""

import pytest

from mcp_guide.tools.tool_document import DocumentRemoveArgs, internal_document_remove


@pytest.fixture
def db(tmp_path):
    return tmp_path / "test_documents.db"


@pytest.mark.anyio
async def test_remove_existing_document(db):
    """Removing an existing document returns success."""
    from mcp_guide.store.document_store import add_document

    await add_document("docs", "readme.md", "/path", "file", "content", db_path=db)

    from unittest.mock import patch

    with patch("mcp_guide.tools.tool_document.remove_document") as mock_remove:
        mock_remove.return_value = True
        result = await internal_document_remove(DocumentRemoveArgs(category="docs", name="readme.md"))

    assert result.success is True
    assert result.value["name"] == "readme.md"


@pytest.mark.anyio
async def test_remove_nonexistent_document():
    """Removing a non-existent document returns failure."""
    from unittest.mock import patch

    with patch("mcp_guide.tools.tool_document.remove_document") as mock_remove:
        mock_remove.return_value = False
        result = await internal_document_remove(DocumentRemoveArgs(category="docs", name="missing.md"))

    assert result.success is False
    assert "not found" in result.error
