"""Integration test: metadata round-trips through DocumentTask into the SQLite store."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_guide.store.document_store import get_document
from mcp_guide.task_manager.interception import EventType
from mcp_guide.tasks.document_task import DocumentTask


@pytest.mark.anyio
async def test_metadata_persisted_through_document_task(tmp_path):
    """Event metadata and frontmatter merge correctly and persist in the store."""
    db = tmp_path / "documents.db"

    project = AsyncMock()
    project.categories = {"docs": object()}
    session = AsyncMock()
    session.get_project = AsyncMock(return_value=project)

    task = DocumentTask(task_manager=MagicMock())

    content = "---\nauthor: Jane\ntags: [guide]\n---\n# Hello"
    event_data = {
        "path": "/tmp/readme.md",
        "content": content,
        "mtime": 1700000000.0,
        "category": "docs",
        "source": "/original/readme.md",
        "metadata": {"author": "Override", "custom-key": "custom-value"},
    }

    async def _get(c, n):
        return await get_document(c, n, db_path=db)

    async def _add(**kw):
        return await _add_with_db(db, **kw)

    with (
        patch("mcp_guide.tasks.document_task.get_session", return_value=session),
        patch("mcp_guide.tasks.document_task.get_document", side_effect=_get),
        patch("mcp_guide.tasks.document_task.add_document", side_effect=_add),
    ):
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


async def _add_with_db(db, **kwargs):
    from mcp_guide.store.document_store import add_document

    return await add_document(**kwargs, db_path=db)
