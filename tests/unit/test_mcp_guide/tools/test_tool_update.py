"""Tests for update tool."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.tools.tool_update import UpdateDocumentsArgs, internal_update_documents


def _set_runtime_docroot(monkeypatch: pytest.MonkeyPatch, root: str | Path) -> None:
    """Point get_runtime().get_docroot() at ``root``."""
    runtime = Mock()
    runtime.get_docroot = AsyncMock(return_value=str(root))
    monkeypatch.setattr("mcp_guide.tools.tool_update.get_runtime", lambda: runtime)


def update_request_context(session) -> SimpleNamespace:
    """Build a RequestContext-shaped object for the update handler."""
    return SimpleNamespace(session=session)


@pytest.mark.anyio
async def test_update_documents_without_bound_project(monkeypatch):
    """Test update_documents works with an unbound session."""
    session = Mock()
    session.task_manager.get_task_by_type.return_value = None
    _set_runtime_docroot(monkeypatch, "/tmp/docroot")
    mock_stats = {"installed": 1, "updated": 0, "patched": 0, "unchanged": 0, "conflicts": 0, "skipped_binary": 0}

    with patch("mcp_guide.tools.tool_update.read_version", new_callable=AsyncMock) as mock_read_version:
        with patch("mcp_guide.tools.tool_update.perform_locked_update", new_callable=AsyncMock) as mock_update:
            mock_read_version.return_value = None
            mock_update.return_value = mock_stats

            result = await internal_update_documents(UpdateDocumentsArgs(), update_request_context(session))

            assert result.success is True
            assert result.value["updated"] is True


@pytest.mark.anyio
async def test_update_documents_already_current_version(tmp_path, monkeypatch):
    """Test update_documents skips update when version is current."""
    session = Mock()
    session.task_manager.get_task_by_type.return_value = None
    _set_runtime_docroot(monkeypatch, tmp_path)

    version_file = tmp_path / ".version"
    with open(version_file, "w") as f:
        from mcp_guide import __version__

        f.write(__version__)

    result = await internal_update_documents(UpdateDocumentsArgs(), update_request_context(session))

    assert result.success is True
    value = result.value
    assert value["updated"] is False
    assert "Already at version" in value["message"]


@pytest.mark.anyio
async def test_update_documents_new_version(tmp_path, monkeypatch):
    """Test update_documents performs update when version differs."""
    session = Mock()
    session.task_manager.get_task_by_type.return_value = None
    _set_runtime_docroot(monkeypatch, tmp_path)

    version_file = tmp_path / ".version"
    with open(version_file, "w") as f:
        f.write("0.0.1")

    mock_stats = {
        "installed": 2,
        "updated": 3,
        "patched": 1,
        "unchanged": 8,
        "conflicts": 0,
        "skipped_binary": 0,
    }

    with patch("mcp_guide.tools.tool_update.perform_locked_update", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = mock_stats

        result = await internal_update_documents(UpdateDocumentsArgs(), update_request_context(session))

        assert result.success is True
        value = result.value
        assert value["updated"] is True
        assert value["stats"] == mock_stats


@pytest.mark.anyio
async def test_update_documents_no_version_file(tmp_path, monkeypatch):
    """Test update_documents performs update when no version file exists."""
    session = Mock()
    session.task_manager.get_task_by_type.return_value = None
    _set_runtime_docroot(monkeypatch, tmp_path)

    mock_stats = {
        "installed": 15,
        "updated": 0,
        "patched": 0,
        "unchanged": 0,
        "conflicts": 0,
        "skipped_binary": 0,
    }

    with patch("mcp_guide.tools.tool_update.perform_locked_update", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = mock_stats

        result = await internal_update_documents(UpdateDocumentsArgs(), update_request_context(session))

        assert result.success is True
        value = result.value
        assert value["updated"] is True
        assert value["stats"]["installed"] == 15


@pytest.mark.anyio
async def test_update_documents_creates_docroot(tmp_path, monkeypatch):
    """Test update_documents delegates to perform_locked_update which creates docroot."""
    session = Mock()
    docroot = tmp_path / "nonexistent" / "docroot"
    session.task_manager.get_task_by_type.return_value = None
    _set_runtime_docroot(monkeypatch, docroot)

    mock_stats = {"installed": 1, "updated": 0, "patched": 0, "unchanged": 0, "conflicts": 0, "skipped_binary": 0}

    with patch("mcp_guide.tools.tool_update.perform_locked_update", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = mock_stats

        result = await internal_update_documents(UpdateDocumentsArgs(), update_request_context(session))

        assert result.success is True
        mock_update.assert_called_once_with(docroot, docroot / ".original.zip")


@pytest.mark.anyio
async def test_update_documents_writes_version_after_update(tmp_path, monkeypatch):
    """Test update_documents writes version file after successful update."""
    session = Mock()
    session.task_manager.get_task_by_type.return_value = None
    _set_runtime_docroot(monkeypatch, tmp_path)

    version_file = tmp_path / ".version"
    with open(version_file, "w") as f:
        f.write("0.0.1")

    mock_stats = {"installed": 0, "updated": 5, "patched": 0, "unchanged": 0, "conflicts": 0, "skipped_binary": 0}

    with patch("mcp_guide.tools.tool_update.perform_locked_update", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = mock_stats

        result = await internal_update_documents(UpdateDocumentsArgs(), update_request_context(session))

        assert result.success is True


@pytest.mark.anyio
async def test_update_documents_acknowledges_pending_update_instruction(tmp_path, monkeypatch):
    """Test update_documents acknowledges the tracked startup update instruction."""
    session = Mock()
    _set_runtime_docroot(monkeypatch, tmp_path)

    mock_stats = {"installed": 1, "updated": 0, "patched": 0, "unchanged": 0, "conflicts": 0, "skipped_binary": 0}
    mock_update_task = Mock()
    mock_update_task.acknowledge_update = AsyncMock()
    mock_task_manager = Mock()
    mock_task_manager.get_task_by_type.return_value = mock_update_task
    session.task_manager = mock_task_manager

    with patch("mcp_guide.tools.tool_update.perform_locked_update", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = mock_stats

        result = await internal_update_documents(UpdateDocumentsArgs(), update_request_context(session))

        assert result.success is True
        mock_update_task.acknowledge_update.assert_called_once()


@pytest.mark.anyio
async def test_update_documents_propagates_docroot_resolution_error(monkeypatch):
    """Test update_documents returns a structured failure for docroot resolution issues."""
    session = Mock()
    runtime = Mock()
    runtime.get_docroot = AsyncMock(side_effect=OSError("docroot unavailable"))
    monkeypatch.setattr("mcp_guide.tools.tool_update.get_runtime", lambda: runtime)

    result = await internal_update_documents(UpdateDocumentsArgs(), update_request_context(session))

    assert result.success is False
    assert result.error_type == "config_read_error"
    assert "docroot unavailable" in result.error
