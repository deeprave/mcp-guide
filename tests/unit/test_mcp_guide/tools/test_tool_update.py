"""Tests for update tool."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.tools.tool_update import UpdateDocumentsArgs, internal_update_documents


@pytest.mark.asyncio
async def test_update_documents_no_project():
    """Test update_documents fails when no project is active."""
    ctx = Mock()

    with patch("mcp_guide.tools.tool_update.get_or_create_session") as mock_session:
        mock_session.side_effect = ValueError("No project")

        result = await internal_update_documents(UpdateDocumentsArgs(), ctx)

        assert result.success is False
        assert result.error_type == "no_project"


@pytest.mark.asyncio
async def test_update_documents_already_current_version(tmp_path):
    """Test update_documents skips update when version is current."""
    ctx = Mock()
    session = Mock()
    session.get_docroot = AsyncMock(return_value=str(tmp_path))

    # Create version file with current version
    version_file = tmp_path / ".version"
    with open(version_file, "w") as f:
        from mcp_guide import __version__

        f.write(__version__)

    with patch("mcp_guide.tools.tool_update.get_or_create_session", return_value=session):
        result = await internal_update_documents(UpdateDocumentsArgs(), ctx)

        assert result.success is True
        value = result.value
        assert value["updated"] is False
        assert "Already at version" in value["message"]


@pytest.mark.asyncio
async def test_update_documents_new_version(tmp_path):
    """Test update_documents performs update when version differs."""
    ctx = Mock()
    session = Mock()
    session.get_docroot = AsyncMock(return_value=str(tmp_path))

    # Create version file with old version
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

    with patch("mcp_guide.tools.tool_update.get_or_create_session", return_value=session):
        with patch("mcp_guide.tools.tool_update.lock_update", new_callable=AsyncMock) as mock_lock:
            mock_lock.return_value = mock_stats

            result = await internal_update_documents(UpdateDocumentsArgs(), ctx)

            assert result.success is True
            value = result.value
            assert value["updated"] is True
            assert value["stats"] == mock_stats


@pytest.mark.asyncio
async def test_update_documents_no_version_file(tmp_path):
    """Test update_documents performs update when no version file exists."""
    ctx = Mock()
    session = Mock()
    session.get_docroot = AsyncMock(return_value=str(tmp_path))

    mock_stats = {
        "installed": 15,
        "updated": 0,
        "patched": 0,
        "unchanged": 0,
        "conflicts": 0,
        "skipped_binary": 0,
    }

    with patch("mcp_guide.tools.tool_update.get_or_create_session", return_value=session):
        with patch("mcp_guide.tools.tool_update.lock_update", new_callable=AsyncMock) as mock_lock:
            mock_lock.return_value = mock_stats

            result = await internal_update_documents(UpdateDocumentsArgs(), ctx)

            assert result.success is True
            value = result.value
            assert value["updated"] is True
            assert value["stats"]["installed"] == 15


@pytest.mark.asyncio
async def test_update_documents_creates_docroot(tmp_path):
    """Test update_documents creates docroot if it doesn't exist."""
    ctx = Mock()
    session = Mock()
    docroot = tmp_path / "nonexistent" / "docroot"
    session.get_docroot = AsyncMock(return_value=str(docroot))

    mock_stats = {"installed": 1, "updated": 0, "patched": 0, "unchanged": 0, "conflicts": 0, "skipped_binary": 0}

    with patch("mcp_guide.tools.tool_update.get_or_create_session", return_value=session):
        with patch("mcp_guide.tools.tool_update.lock_update", new_callable=AsyncMock) as mock_lock:
            with patch("mcp_guide.tools.tool_update.write_version", new_callable=AsyncMock) as mock_write:
                mock_lock.return_value = mock_stats

                result = await internal_update_documents(UpdateDocumentsArgs(), ctx)

                assert result.success is True
                assert docroot.exists()
                # Verify version was written
                mock_write.assert_called_once()


@pytest.mark.asyncio
async def test_update_documents_writes_version_after_update(tmp_path):
    """Test update_documents writes version file after successful update."""
    ctx = Mock()
    session = Mock()
    session.get_docroot = AsyncMock(return_value=str(tmp_path))

    # Create old version file
    version_file = tmp_path / ".version"
    with open(version_file, "w") as f:
        f.write("0.0.1")

    mock_stats = {"installed": 0, "updated": 5, "patched": 0, "unchanged": 0, "conflicts": 0, "skipped_binary": 0}

    with patch("mcp_guide.tools.tool_update.get_or_create_session", return_value=session):
        with patch("mcp_guide.tools.tool_update.lock_update", new_callable=AsyncMock) as mock_lock:
            with patch("mcp_guide.tools.tool_update.write_version", new_callable=AsyncMock) as mock_write:
                mock_lock.return_value = mock_stats

                result = await internal_update_documents(UpdateDocumentsArgs(), ctx)

                assert result.success is True
                # Verify write_version was called with correct arguments
                from mcp_guide import __version__

                mock_write.assert_called_once_with(tmp_path, __version__)
