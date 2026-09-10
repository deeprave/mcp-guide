"""Document ingestion uses the owning project and persists through real SQLite."""

from dataclasses import replace

import pytest
from tests.helpers import create_bound_test_session

from mcp_guide.models import Category
from mcp_guide.store.document_store import get_document, get_document_content, list_documents
from mcp_guide.task_manager import EventType, TaskManager
from mcp_guide.tasks.document_task import DocumentTask


@pytest.fixture
async def task(runtime, tmp_path, monkeypatch):
    runtime.configuration_service().config_file.write_text("projects: {}\n")
    monkeypatch.setattr("mcp_guide.store.document_store.get_documents_db", lambda: tmp_path / "documents.db")
    session = await create_bound_test_session(runtime, "documents")
    await session.save_project(
        replace(await session.get_project(), categories={"docs": Category(dir="docs", patterns=["*"])})
    )
    manager = TaskManager(session)
    task = DocumentTask(manager, session)
    yield task
    await manager.cleanup()


def event(**changes):
    return {
        "path": "/tmp/readme.md",
        "content": "# Hello",
        "mtime": 1700000000,
        "category": "docs",
        "source": "/original/readme.md",
        **changes,
    }


@pytest.mark.anyio
async def test_ingestion_round_trip_skip_update_force_and_metadata(task, runtime):
    # A different current runtime project cannot replace this task's explicit owner.
    await create_bound_test_session(runtime, "other")
    data = event(
        content="---\ntitle: Frontmatter\nauthor: Someone\n---\n# Hello",
        metadata={"title": "Event", "type": "ignored", "content-type": "ignored"},
    )
    results = await task.task_manager.dispatch_event(EventType.FS_FILE_CONTENT, data)
    assert len(results) == 1 and results[0].result
    record = await get_document("docs", "readme.md")
    assert (record.name, record.source, record.source_type, record.mtime) == (
        "readme.md",
        "/original/readme.md",
        "file",
        1700000000.0,
    )
    assert record.metadata == {
        "title": "Event",
        "author": "Someone",
        "type": "agent/instruction",
        "content-type": "text/markdown",
    }
    assert await get_document_content("docs", "readme.md") == "# Hello"
    skipped = await task.handle_event(EventType.FS_FILE_CONTENT, event(content="Wrong"))
    assert not skipped.result
    assert skipped.message == "Document docs/readme.md unchanged (same mtime)"
    assert await get_document_content("docs", "readme.md") == "# Hello"
    updated = await task.handle_event(EventType.FS_FILE_CONTENT, event(content="New", mtime=1700000001))
    assert updated.result
    assert await get_document_content("docs", "readme.md") == "New"
    forced = await task.handle_event(EventType.FS_FILE_CONTENT, event(content="Forced", force=True))
    assert forced.result
    assert await get_document_content("docs", "readme.md") == "Forced"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "changes,name,source,source_type",
    [
        ({"path": "/some/dir/guide.md"}, "guide.md", "/original/readme.md", "file"),
        (
            {"name": "custom/doc.md", "source": "https://example.com/readme.md"},
            "custom/doc.md",
            "https://example.com/readme.md",
            "url",
        ),
        ({"source": 42}, "readme.md", "file", "file"),
        ({"omit_source": True}, "readme.md", "file", "file"),
    ],
    ids=["basename", "explicit-name-url", "invalid-source-default", "missing-source-default"],
)
async def test_ingestion_name_and_source_mapping(task, changes, name, source, source_type):
    data = event(**changes)
    if data.pop("omit_source", False):
        data.pop("source")
    result = await task.handle_event(EventType.FS_FILE_CONTENT, data)
    assert result.result
    record = await get_document("docs", name)
    assert (record.name, record.source, record.source_type) == (name, source, source_type)
    assert await get_document_content("docs", name) == "# Hello"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "changes,message",
    [
        ({"category": "missing"}, "does not exist"),
        ({"mtime": "not-a-number"}, "mtime must be numeric"),
        ({"mtime": True}, "mtime must be numeric"),
        ({"name": "unsafe\r\nname.md"}, "control character"),
    ],
)
async def test_invalid_ingestion_is_rejected_without_writing(task, changes, message):
    result = await task.handle_event(EventType.FS_FILE_CONTENT, event(**changes))
    assert not result.result
    assert message in result.message
    assert await list_documents() == []


@pytest.mark.anyio
async def test_unrelated_or_unclassified_events_are_ignored(task):
    assert await task.handle_event(EventType.FS_DIRECTORY, event()) is None
    assert await task.handle_event(EventType.FS_FILE_CONTENT, {"path": "/tmp/file.md", "content": "hi"}) is None
    assert await task.handle_event(EventType.FS_FILE_CONTENT, event(category=123)) is None
    assert await list_documents() == []
