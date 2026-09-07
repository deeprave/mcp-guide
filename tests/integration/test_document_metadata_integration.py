"""Integration test: metadata round-trips through DocumentTask into the SQLite store."""

import pytest

from mcp_guide.models import Category
from mcp_guide.store.document_store import get_document
from mcp_guide.task_manager.interception import EventType
from mcp_guide.tasks.document_task import DocumentTask
from tests.helpers import create_bound_test_session


@pytest.mark.anyio
async def test_metadata_persisted_through_document_task(runtime, tmp_path, monkeypatch):
    """Event metadata and frontmatter merge correctly and persist in the store."""
    db = tmp_path / "documents.db"

    # Select an isolated database without mocking ingestion or persistence.
    monkeypatch.setattr("mcp_guide.store.document_store.get_documents_db", lambda: db)
    session = await create_bound_test_session(runtime, "metadata")
    await session.update_config(lambda p: p.with_category("docs", Category(dir="docs", patterns=["*.md"])))
    task = DocumentTask(task_manager=session.task_manager, session=session)

    content = "---\nauthor: Jane\ntags: [guide]\n---\n# Hello"
    event_data = {
        "path": "/tmp/readme.md",
        "content": content,
        "mtime": 1700000000.0,
        "category": "docs",
        "source": "/original/readme.md",
        "metadata": {"author": "Override", "custom-key": "custom-value"},
    }

    result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

    assert result is not None
    assert result.result is True

    record = await get_document("docs", "readme.md", db_path=db)
    assert record is not None
    # Event metadata overrides frontmatter
    assert record.metadata["author"] == "Override"
    # Event-only key persisted
    assert record.metadata["custom-key"] == "custom-value"
    # Frontmatter key not overridden by event survives
    assert record.metadata["tags"] == ["guide"]
    # Auto-detected fields present
    assert "content-type" in record.metadata
    assert record.metadata["type"] == "agent/instruction"
