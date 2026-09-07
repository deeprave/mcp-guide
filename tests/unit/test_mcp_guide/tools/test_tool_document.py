"""Document removal uses the store and reports repeat removal as missing."""

import pytest
from tests.helpers import create_unbound_test_session, request_context_for

from mcp_guide.store.document_store import add_document, get_document
from mcp_guide.tools.tool_document import DocumentRemoveArgs, internal_document_remove


@pytest.mark.anyio
async def test_remove_document_persists_deletion_and_reports_missing(runtime, tmp_path, monkeypatch):
    # Isolate the database location, not the persistence operations.
    monkeypatch.setattr("mcp_guide.store.document_store.get_documents_db", lambda: tmp_path / "documents.db")
    await add_document("docs", "readme.md", "/path", "file", "content")
    await add_document("other", "readme.md", "/other", "file", "keep")
    context = await request_context_for(create_unbound_test_session(runtime))
    args = DocumentRemoveArgs(category="docs", name="readme.md")

    result = await internal_document_remove(args, context)
    assert result.success is True
    assert result.value == {"category": "docs", "name": "readme.md"}
    assert await get_document("docs", "readme.md") is None
    assert await get_document("other", "readme.md") is not None

    result = await internal_document_remove(args, context)
    assert result.success is False
    assert result.error_type == "not_found"
    assert result.error == "Document docs/readme.md not found"
