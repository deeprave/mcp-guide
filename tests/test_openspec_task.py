"""Tests for OpenSpec CLI detection task."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_guide.client_context.openspec_task import OpenSpecTask
from mcp_guide.task_manager import EventType


@pytest.fixture
def mock_task_manager():
    """Create a mock task manager."""
    manager = MagicMock()
    manager.subscribe = MagicMock()  # Synchronous
    manager.unsubscribe = AsyncMock()
    manager.queue_instruction = AsyncMock()
    manager.set_cached_data = MagicMock()
    return manager


@pytest.fixture
def mock_session():
    """Create a mock session with feature flags."""
    session = MagicMock()
    flags_mock = MagicMock()
    flags_mock.list = AsyncMock(return_value={"openspec": True})
    session.feature_flags.return_value = flags_mock
    return session


class TestOpenSpecTask:
    """Test OpenSpec CLI detection task."""

    @pytest.mark.asyncio
    async def test_init_subscribes_to_events(self, mock_task_manager):
        """Test that task subscribes to TIMER_ONCE and FS_COMMAND events."""
        task = OpenSpecTask(mock_task_manager)

        mock_task_manager.subscribe.assert_called_once()
        call_args = mock_task_manager.subscribe.call_args
        assert call_args[0][0] == task
        assert call_args[0][1] & EventType.TIMER_ONCE
        assert call_args[0][1] & EventType.FS_COMMAND

    @pytest.mark.asyncio
    async def test_get_name(self, mock_task_manager):
        """Test task name."""
        task = OpenSpecTask(mock_task_manager)
        assert task.get_name() == "OpenSpecTask"

    @pytest.mark.asyncio
    async def test_on_tool_unsubscribes_when_flag_disabled(self, mock_task_manager):
        """Test that task unsubscribes when openspec flag is disabled."""
        task = OpenSpecTask(mock_task_manager)

        with patch("mcp_guide.session.get_or_create_session") as mock_get_session:
            session = MagicMock()
            flags_mock = MagicMock()
            flags_mock.list = AsyncMock(return_value={"openspec": False})
            session.feature_flags.return_value = flags_mock
            mock_get_session.return_value = session

            await task.on_tool()

            mock_task_manager.unsubscribe.assert_called_once_with(task)

    @pytest.mark.asyncio
    async def test_on_tool_continues_when_flag_enabled(self, mock_task_manager):
        """Test that task continues when openspec flag is enabled."""
        task = OpenSpecTask(mock_task_manager)

        with patch("mcp_guide.utils.flag_utils.get_resolved_flag_value") as mock_get_flag:
            mock_get_flag.return_value = True

            await task.on_tool()

            mock_task_manager.unsubscribe.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_event_timer_once_requests_cli_check(self, mock_task_manager):
        """Test that TIMER_ONCE event requests CLI availability check."""
        task = OpenSpecTask(mock_task_manager)

        with patch("mcp_guide.client_context.openspec_task.render_common_template") as mock_render:
            mock_render.return_value = "check cli instruction"

            result = await task.handle_event(EventType.TIMER_ONCE, {})

            assert result is True
            mock_task_manager.queue_instruction.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_event_cli_found(self, mock_task_manager):
        """Test handling CLI found response."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {"command": "openspec", "path": "/usr/local/bin/openspec", "found": True}

        result = await task.handle_event(EventType.FS_COMMAND, event_data)

        assert result is True
        assert task.is_available() is True
        mock_task_manager.set_cached_data.assert_called_once_with("openspec_available", True)

    @pytest.mark.asyncio
    async def test_handle_event_cli_not_found(self, mock_task_manager):
        """Test handling CLI not found response."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {"command": "openspec", "path": None, "found": False}

        result = await task.handle_event(EventType.FS_COMMAND, event_data)

        assert result is True
        assert task.is_available() is False
        mock_task_manager.set_cached_data.assert_called_once_with("openspec_available", False)

    @pytest.mark.asyncio
    async def test_is_available_returns_none_before_check(self, mock_task_manager):
        """Test that is_available returns None before CLI check completes."""
        task = OpenSpecTask(mock_task_manager)
        assert task.is_available() is None

    @pytest.mark.asyncio
    async def test_handle_event_ignores_other_files(self, mock_task_manager):
        """Test that task ignores file content events for other files."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {"path": ".some-other-file.txt", "content": "content"}

        result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result is False
        mock_task_manager.set_cached_data.assert_not_called()
