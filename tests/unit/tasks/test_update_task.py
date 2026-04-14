"""Tests for McpUpdateTask."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.task_manager.interception import EventType
from mcp_guide.tasks.update_task import McpUpdateTask


@pytest.mark.anyio
async def test_update_task_enabled_without_flag():
    """Test task treats unset autoupdate as enabled."""
    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.resolved_flags = AsyncMock(return_value={})
    task_manager.queue_instruction_with_ack = AsyncMock(return_value="test-id")
    task_manager.unsubscribe = AsyncMock()

    session = Mock()
    session.get_docroot = AsyncMock(return_value="/tmp/docroot")

    with patch("mcp_guide.session.get_session", return_value=session):
        with patch("mcp_guide.render.rendering.render_content", new_callable=AsyncMock) as mock_render:
            with patch("mcp_guide.tasks.update_task.AsyncPath.exists", new=AsyncMock(return_value=True)):
                mock_content = Mock()
                mock_content.content = "Update prompt"
                mock_render.return_value = mock_content

                task = McpUpdateTask(task_manager)
                result = await task.handle_event(EventType.TIMER_ONCE, {})

                task_manager.resolved_flags.assert_called_once()
                task_manager.queue_instruction_with_ack.assert_called_once_with("Update prompt")
                assert result is not None
                assert result.result is True


@pytest.mark.anyio
async def test_update_task_disabled_with_explicit_false():
    """Test task is disabled only when autoupdate is explicitly false."""
    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.resolved_flags = AsyncMock(return_value={"autoupdate": False})
    task_manager.queue_instruction_with_ack = AsyncMock()
    task_manager.unsubscribe = AsyncMock()

    task = McpUpdateTask(task_manager)
    result = await task.handle_event(EventType.TIMER_ONCE, {})

    task_manager.resolved_flags.assert_called_once()
    task_manager.queue_instruction_with_ack.assert_not_called()
    assert result is not None
    assert result.result is True


@pytest.mark.anyio
async def test_update_task_no_project():
    """Test task handles missing project gracefully."""
    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.resolved_flags = AsyncMock(return_value={})
    task_manager.unsubscribe = AsyncMock()

    with patch("mcp_guide.session.get_session") as mock_session:
        mock_session.side_effect = ValueError("No project")

        task = McpUpdateTask(task_manager)
        result = await task.handle_event(EventType.TIMER_ONCE, {})

        # Should not crash
        task_manager.resolved_flags.assert_called_once()
        assert result is not None
        assert result.result is True


@pytest.mark.anyio
async def test_update_task_no_version_file(tmp_path):
    """Test task prompts when no version file exists."""
    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.resolved_flags = AsyncMock(return_value={})
    task_manager.queue_instruction_with_ack = AsyncMock(return_value="test-id")
    task_manager.unsubscribe = AsyncMock()

    session = Mock()
    session.get_docroot = AsyncMock(return_value=str(tmp_path))

    with patch("mcp_guide.session.get_session", return_value=session):
        with patch("mcp_guide.render.rendering.render_content", new_callable=AsyncMock) as mock_render:
            mock_content = Mock()
            mock_content.content = "Update prompt"
            mock_render.return_value = mock_content

            task = McpUpdateTask(task_manager)
            result = await task.handle_event(EventType.TIMER_ONCE, {})

            # Should queue instruction
            task_manager.queue_instruction_with_ack.assert_called_once_with("Update prompt")
            assert result is not None
            assert result.result is True


@pytest.mark.anyio
async def test_update_task_version_mismatch(tmp_path):
    """Test task prompts when version differs."""
    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.resolved_flags = AsyncMock(return_value={"autoupdate": True})
    task_manager.queue_instruction_with_ack = AsyncMock(return_value="test-id")
    task_manager.unsubscribe = AsyncMock()

    session = Mock()
    session.get_docroot = AsyncMock(return_value=str(tmp_path))

    # Create version file with old version
    version_file = tmp_path / ".version"
    with open(version_file, "w") as f:
        f.write("0.0.1")

    with patch("mcp_guide.session.get_session", return_value=session):
        with patch("mcp_guide.render.rendering.render_content", new_callable=AsyncMock) as mock_render:
            mock_content = Mock()
            mock_content.content = "Update prompt"
            mock_render.return_value = mock_content

            task = McpUpdateTask(task_manager)
            result = await task.handle_event(EventType.TIMER_ONCE, {})

            # Should queue instruction
            task_manager.queue_instruction_with_ack.assert_called_once()
            assert result is not None
            assert result.result is True


@pytest.mark.anyio
async def test_update_task_version_current(tmp_path):
    """Test task skips prompt when version is current."""
    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.resolved_flags = AsyncMock(return_value={"autoupdate": True})
    task_manager.queue_instruction_with_ack = AsyncMock()
    task_manager.unsubscribe = AsyncMock()

    session = Mock()
    session.get_docroot = AsyncMock(return_value=str(tmp_path))

    # Create version file with current version
    version_file = tmp_path / ".version"
    with open(version_file, "w") as f:
        from mcp_guide import __version__

        f.write(__version__)

    with patch("mcp_guide.session.get_session", return_value=session):
        task = McpUpdateTask(task_manager)
        result = await task.handle_event(EventType.TIMER_ONCE, {})

        # Should NOT queue instruction
        task_manager.queue_instruction_with_ack.assert_not_called()
        assert result is not None
        assert result.result is True


@pytest.mark.anyio
async def test_acknowledge_update_clears_tracked_instruction():
    """Test acknowledge_update acknowledges and clears the tracked instruction id."""
    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.acknowledge_instruction = AsyncMock()

    task = McpUpdateTask(task_manager)
    task._instruction_id = "tracked-id"

    await task.acknowledge_update()

    task_manager.acknowledge_instruction.assert_called_once_with("tracked-id")
    assert task._instruction_id is None
