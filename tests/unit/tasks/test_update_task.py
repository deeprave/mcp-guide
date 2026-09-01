"""Tests for McpUpdateTask."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.task_manager.interception import EventType
from mcp_guide.tasks.update_task import McpUpdateTask


@pytest.mark.anyio
async def test_update_task_enabled_without_flag(tmp_path):
    """Test task treats unset autoupdate as enabled when an update is needed."""
    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.resolved_flags = AsyncMock(return_value={})
    task_manager.queue_instruction_with_ack = AsyncMock(return_value="test-id")
    task_manager.unsubscribe = AsyncMock()

    session = Mock()
    session.runtime.get_docroot = AsyncMock(return_value=str(tmp_path))

    version_file = tmp_path / ".version"
    version_file.write_text("0.0.1")

    with patch("mcp_guide.render.rendering.render_content", new_callable=AsyncMock) as mock_render:
        mock_content = Mock()
        mock_content.content = "Update prompt"
        mock_render.return_value = mock_content

        task = McpUpdateTask(task_manager, session=session)
        result = await task.handle_event(EventType.TIMER_ONCE, {})

        task_manager.resolved_flags.assert_called_once_with(session)
        task_manager.queue_instruction_with_ack.assert_called_once_with("Update prompt")
        assert result is not None
        assert result.result is True


@pytest.mark.anyio
async def test_update_task_uses_owning_session_without_ambient_lookup(tmp_path):
    """A session-owned update task does not consult ambient request state."""
    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.resolved_flags = AsyncMock(return_value={"autoupdate": False})
    task_manager.unsubscribe = AsyncMock()
    session = Mock()

    with patch("mcp_guide.session.get_session") as get_session:
        task = McpUpdateTask(task_manager, session=session)
        result = await task.handle_event(EventType.TIMER_ONCE, {})

    assert result is not None and result.result is True
    get_session.assert_not_called()


@pytest.mark.anyio
async def test_update_task_disabled_with_explicit_false():
    """Test task is disabled only when autoupdate is explicitly false."""
    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.resolved_flags = AsyncMock(return_value={"autoupdate": False})
    task_manager.queue_instruction_with_ack = AsyncMock()
    task_manager.unsubscribe = AsyncMock()

    task = McpUpdateTask(task_manager, session=Mock())
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

    session = Mock()
    session.runtime.get_docroot = AsyncMock(return_value="/missing-docroot")
    task = McpUpdateTask(task_manager, session=session)
    result = await task.handle_event(EventType.TIMER_ONCE, {})

    task_manager.resolved_flags.assert_called_once_with(session)
    assert result is not None
    assert result.result is True


@pytest.mark.anyio
async def test_update_task_no_version_file(tmp_path):
    """Test task skips prompt when no version file exists."""
    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.resolved_flags = AsyncMock(return_value={})
    task_manager.queue_instruction_with_ack = AsyncMock()
    task_manager.unsubscribe = AsyncMock()

    session = Mock()
    session.runtime.get_docroot = AsyncMock(return_value=str(tmp_path))

    task = McpUpdateTask(task_manager, session=session)
    result = await task.handle_event(EventType.TIMER_ONCE, {})

    task_manager.queue_instruction_with_ack.assert_not_called()
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
    session.runtime.get_docroot = AsyncMock(return_value=str(tmp_path))

    # Create version file with old version
    version_file = tmp_path / ".version"
    with open(version_file, "w") as f:
        f.write("0.0.1")

    with patch("mcp_guide.render.rendering.render_content", new_callable=AsyncMock) as mock_render:
        mock_content = Mock()
        mock_content.content = "Update prompt"
        mock_render.return_value = mock_content

        task = McpUpdateTask(task_manager, session=session)
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
    session.runtime.get_docroot = AsyncMock(return_value=str(tmp_path))

    # Create version file with current version
    version_file = tmp_path / ".version"
    with open(version_file, "w") as f:
        from mcp_guide import __version__

        f.write(__version__)

    task = McpUpdateTask(task_manager, session=session)
    result = await task.handle_event(EventType.TIMER_ONCE, {})

    # Should NOT queue instruction
    task_manager.queue_instruction_with_ack.assert_not_called()
    assert result is not None
    assert result.result is True


@pytest.mark.anyio
async def test_update_task_skips_prompt_for_unsafe_docroot(tmp_path) -> None:
    """Test task skips prompt when docroot is not safe for updates."""
    from mcp_guide.installer.core import DocrootValidationError

    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.resolved_flags = AsyncMock(return_value={"autoupdate": True})
    task_manager.queue_instruction_with_ack = AsyncMock()
    task_manager.unsubscribe = AsyncMock()

    session = Mock()
    session.runtime.get_docroot = AsyncMock(return_value=str(tmp_path))

    with (
        patch("mcp_guide.tasks.update_task.AsyncPath.exists", new=AsyncMock(return_value=True)),
        patch(
            "mcp_guide.tasks.update_task.validate_docroot_safety",
            new=AsyncMock(side_effect=DocrootValidationError("unsafe")),
        ),
    ):
        task = McpUpdateTask(task_manager, session=session)
        result = await task.handle_event(EventType.TIMER_ONCE, {})

        task_manager.queue_instruction_with_ack.assert_not_called()
        assert result is not None
        assert result.result is True


@pytest.mark.anyio
async def test_update_task_skips_prompt_when_templates_missing(tmp_path) -> None:
    """Test task skips prompt when template validation cannot locate templates."""
    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.resolved_flags = AsyncMock(return_value={"autoupdate": True})
    task_manager.queue_instruction_with_ack = AsyncMock()
    task_manager.unsubscribe = AsyncMock()

    session = Mock()
    session.runtime.get_docroot = AsyncMock(return_value=str(tmp_path))

    version_file = tmp_path / ".version"
    version_file.write_text("0.0.1")

    with (
        patch(
            "mcp_guide.tasks.update_task.validate_docroot_safety",
            new=AsyncMock(side_effect=FileNotFoundError("Templates directory not found")),
        ),
    ):
        task = McpUpdateTask(task_manager, session=session)
        result = await task.handle_event(EventType.TIMER_ONCE, {})

        task_manager.queue_instruction_with_ack.assert_not_called()
        assert result is not None
        assert result.result is True


@pytest.mark.anyio
async def test_acknowledge_update_clears_tracked_instruction():
    """Test acknowledge_update acknowledges and clears the tracked instruction id."""
    task_manager = Mock()
    task_manager.subscribe = Mock()
    task_manager.acknowledge_instruction = AsyncMock()

    task = McpUpdateTask(task_manager, session=Mock())
    task._instruction_id = "tracked-id"

    await task.acknowledge_update()

    task_manager.acknowledge_instruction.assert_called_once_with("tracked-id")
    assert task._instruction_id is None
