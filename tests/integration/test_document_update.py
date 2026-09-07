"""Document update behaviour through real project validation and SQLite state."""

import pytest
from pydantic import ValidationError

from mcp_guide.models import Category
from mcp_guide.store.document_store import add_document, get_document, get_document_content
from mcp_guide.tools.tool_document_update import DocumentUpdateArgs, internal_document_update
from tests.helpers import create_bound_test_session, request_context_for


@pytest.mark.anyio
async def test_document_update_persists_mutations_and_preserves_state_on_errors(runtime, tmp_path, monkeypatch):
    # Redirect the database location while exercising real storage operations.
    monkeypatch.setattr("mcp_guide.store.document_store.get_documents_db", lambda: tmp_path / "documents.db")
    session = await create_bound_test_session(runtime, "documents")
    await session.update_config(lambda p: p.with_category("docs", Category(dir="docs", patterns=["*.md"])))
    context = await request_context_for(session)
    await add_document("docs", "old.md", "/source", "file", "content", metadata={"a": "1"})
    await add_document("docs", "occupied.md", "/occupied", "file", "keep")

    async def update(name="old.md", **mutations):
        return await internal_document_update(DocumentUpdateArgs(category="docs", name=name, **mutations), context)

    missing_category = await update(new_category="nonexistent")
    assert not missing_category.success
    assert "does not exist" in missing_category.error
    collision = await update(new_name="occupied.md")
    assert not collision.success
    assert "already exists" in collision.error
    assert await get_document_content("docs", "old.md") == "content"
    assert await get_document_content("docs", "occupied.md") == "keep"

    renamed = await update(new_name="new.md", metadata_add={"b": "2"})
    assert renamed.success
    assert renamed.value == {"category": "docs", "name": "new.md", "metadata": {"a": "1", "b": "2"}}
    assert await get_document("docs", "old.md") is None
    stored = await get_document("docs", "new.md")
    assert stored.metadata == renamed.value["metadata"]
    assert await get_document_content("docs", "new.md") == "content"

    missing = await update(new_name="x.md")
    assert not missing.success
    assert missing.error_type == "not_found"


def test_metadata_mutations_are_mutually_exclusive():
    with pytest.raises(ValidationError, match="mutually exclusive"):
        DocumentUpdateArgs(category="docs", name="file.md", metadata_add={"a": "1"}, metadata_clear=["b"])
