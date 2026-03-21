"""Tests for DocumentTask document ingestion."""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_guide.store.document_store import DocumentRecord
from mcp_guide.task_manager.interception import EventType
from mcp_guide.tasks.document_task import DocumentTask


def _make_project(categories=None):
    """Create a mock project with given category names."""
    project = AsyncMock()
    project.categories = categories or {}
    return project


def _make_session(project):
    """Create a mock session returning the given project."""
    session = AsyncMock()
    session.get_project = AsyncMock(return_value=project)
    return session


def _base_event_data(**overrides):
    """Build a minimal valid event data dict."""
    data = {
        "path": "/tmp/readme.md",
        "content": "# Hello",
        "mtime": 1700000000.0,
        "category": "docs",
        "source": "/original/readme.md",
    }
    data.update(overrides)
    return data


@pytest.fixture
def task():
    from unittest.mock import MagicMock

    tm = MagicMock()
    return DocumentTask(task_manager=tm)


@pytest.mark.anyio
async def test_ignores_event_without_required_metadata(task):
    """Events without category+source metadata are not matched."""
    result = await task.handle_event(EventType.FS_FILE_CONTENT, {"path": "/tmp/file.md", "content": "hi"})
    assert result is None


@pytest.mark.anyio
async def test_ingest_new_document(task):
    """New document is stored successfully."""
    project = _make_project(categories={"docs": object()})
    session = _make_session(project)
    record = DocumentRecord(
        id=1,
        category="docs",
        name="readme.md",
        source="/original/readme.md",
        source_type="file",
        metadata={},
        created_at="",
        updated_at="",
        content="# Hello",
        mtime=1700000000.0,
    )

    with (
        patch("mcp_guide.tasks.document_task.get_session", return_value=session),
        patch("mcp_guide.tasks.document_task.get_document", return_value=None),
        patch("mcp_guide.tasks.document_task.add_document", return_value=record) as mock_add,
    ):
        result = await task.handle_event(EventType.FS_FILE_CONTENT, _base_event_data())

    assert result is not None
    assert result.result is True
    mock_add.assert_called_once()
    call_kwargs = mock_add.call_args
    assert call_kwargs.kwargs["category"] == "docs"
    assert call_kwargs.kwargs["name"] == "readme.md"
    assert call_kwargs.kwargs["mtime"] == 1700000000.0


@pytest.mark.anyio
async def test_rejects_same_mtime(task):
    """Document with same mtime is rejected."""
    project = _make_project(categories={"docs": object()})
    session = _make_session(project)
    existing = DocumentRecord(
        id=1,
        category="docs",
        name="readme.md",
        source="/path",
        source_type="file",
        metadata={},
        created_at="",
        updated_at="",
        mtime=1700000000.0,
    )

    with (
        patch("mcp_guide.tasks.document_task.get_session", return_value=session),
        patch("mcp_guide.tasks.document_task.get_document", return_value=existing),
    ):
        result = await task.handle_event(EventType.FS_FILE_CONTENT, _base_event_data())

    assert result is not None
    assert result.result is False
    assert "unchanged" in result.message


@pytest.mark.anyio
async def test_updates_newer_mtime(task):
    """Document with newer mtime is updated."""
    project = _make_project(categories={"docs": object()})
    session = _make_session(project)
    existing = DocumentRecord(
        id=1,
        category="docs",
        name="readme.md",
        source="/path",
        source_type="file",
        metadata={},
        created_at="",
        updated_at="",
        mtime=1600000000.0,
    )
    updated = DocumentRecord(
        id=1,
        category="docs",
        name="readme.md",
        source="/original/readme.md",
        source_type="file",
        metadata={},
        created_at="",
        updated_at="",
        content="# Hello",
        mtime=1700000000.0,
    )

    with (
        patch("mcp_guide.tasks.document_task.get_session", return_value=session),
        patch("mcp_guide.tasks.document_task.get_document", return_value=existing),
        patch("mcp_guide.tasks.document_task.add_document", return_value=updated),
    ):
        result = await task.handle_event(EventType.FS_FILE_CONTENT, _base_event_data())

    assert result is not None
    assert result.result is True


@pytest.mark.anyio
async def test_force_overwrite_bypasses_mtime(task):
    """Force flag bypasses mtime check."""
    project = _make_project(categories={"docs": object()})
    session = _make_session(project)
    record = DocumentRecord(
        id=1,
        category="docs",
        name="readme.md",
        source="/original/readme.md",
        source_type="file",
        metadata={},
        created_at="",
        updated_at="",
        content="# Hello",
        mtime=1700000000.0,
    )

    with (
        patch("mcp_guide.tasks.document_task.get_session", return_value=session),
        patch("mcp_guide.tasks.document_task.add_document", return_value=record) as mock_add,
    ):
        result = await task.handle_event(EventType.FS_FILE_CONTENT, _base_event_data(force=True))

    assert result is not None
    assert result.result is True
    mock_add.assert_called_once()


@pytest.mark.anyio
async def test_invalid_category_rejected(task):
    """Non-existent category returns error."""
    project = _make_project(categories={})
    session = _make_session(project)

    with patch("mcp_guide.tasks.document_task.get_session", return_value=session):
        result = await task.handle_event(EventType.FS_FILE_CONTENT, _base_event_data())

    assert result is not None
    assert result.result is False
    assert "does not exist" in result.message


@pytest.mark.anyio
async def test_name_defaults_to_path_basename(task):
    """Document name defaults to basename of path."""
    project = _make_project(categories={"docs": object()})
    session = _make_session(project)
    record = DocumentRecord(
        id=1,
        category="docs",
        name="guide.md",
        source="/src/guide.md",
        source_type="file",
        metadata={},
        created_at="",
        updated_at="",
        content="text",
        mtime=100.0,
    )

    with (
        patch("mcp_guide.tasks.document_task.get_session", return_value=session),
        patch("mcp_guide.tasks.document_task.get_document", return_value=None),
        patch("mcp_guide.tasks.document_task.add_document", return_value=record) as mock_add,
    ):
        result = await task.handle_event(
            EventType.FS_FILE_CONTENT,
            _base_event_data(path="/some/dir/guide.md"),
        )

    assert result.result is True
    assert mock_add.call_args.kwargs["name"] == "guide.md"


@pytest.mark.anyio
async def test_name_override(task):
    """Explicit name in event data overrides path basename."""
    project = _make_project(categories={"docs": object()})
    session = _make_session(project)
    record = DocumentRecord(
        id=1,
        category="docs",
        name="custom/doc.md",
        source="/src/file.md",
        source_type="file",
        metadata={},
        created_at="",
        updated_at="",
        content="text",
        mtime=100.0,
    )

    with (
        patch("mcp_guide.tasks.document_task.get_session", return_value=session),
        patch("mcp_guide.tasks.document_task.get_document", return_value=None),
        patch("mcp_guide.tasks.document_task.add_document", return_value=record) as mock_add,
    ):
        result = await task.handle_event(
            EventType.FS_FILE_CONTENT,
            _base_event_data(name="custom/doc.md"),
        )

    assert result.result is True
    assert mock_add.call_args.kwargs["name"] == "custom/doc.md"


@pytest.mark.anyio
async def test_url_source_type_detected(task):
    """Source starting with http:// or https:// sets source_type to url."""
    project = _make_project(categories={"docs": object()})
    session = _make_session(project)
    record = DocumentRecord(
        id=1,
        category="docs",
        name="readme.md",
        source="https://example.com/readme.md",
        source_type="url",
        metadata={},
        created_at="",
        updated_at="",
        content="# Hello",
        mtime=100.0,
    )

    with (
        patch("mcp_guide.tasks.document_task.get_session", return_value=session),
        patch("mcp_guide.tasks.document_task.get_document", return_value=None),
        patch("mcp_guide.tasks.document_task.add_document", return_value=record) as mock_add,
    ):
        result = await task.handle_event(
            EventType.FS_FILE_CONTENT,
            _base_event_data(source="https://example.com/readme.md"),
        )

    assert result.result is True
    assert mock_add.call_args.kwargs["source_type"] == "url"
