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
        from unittest.mock import AsyncMock

        task = OpenSpecTask(mock_task_manager)

        with patch("mcp_guide.utils.flag_utils.get_resolved_flag_value", new_callable=AsyncMock) as mock_get_flag:
            mock_get_flag.return_value = False

            await task.on_tool()

            mock_task_manager.unsubscribe.assert_called_once_with(task)

    @pytest.mark.asyncio
    async def test_on_tool_continues_when_flag_enabled(self, mock_task_manager):
        """Test that task continues when openspec flag is enabled."""
        from unittest.mock import AsyncMock

        task = OpenSpecTask(mock_task_manager)

        with patch("mcp_guide.utils.flag_utils.get_resolved_flag_value", new_callable=AsyncMock) as mock_get_flag:
            mock_get_flag.return_value = True

            await task.on_tool()

            mock_task_manager.unsubscribe.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_event_timer_once_requests_cli_check(self, mock_task_manager):
        """Test that TIMER_ONCE event requests CLI availability check."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True  # Simulate flag already checked

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

        with patch.object(task, "request_project_check", new_callable=AsyncMock) as mock_request:
            result = await task.handle_event(EventType.FS_COMMAND, event_data)

            assert result is True
            assert task.is_available() is True
            mock_task_manager.set_cached_data.assert_called_once_with("openspec_available", True)
            mock_request.assert_called_once()

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
    async def test_handle_event_ignores_unsubscribed_events(self, mock_task_manager):
        """Test that task ignores events it doesn't subscribe to."""
        task = OpenSpecTask(mock_task_manager)

        # Task only subscribes to TIMER_ONCE, FS_COMMAND, and FS_DIRECTORY, not FS_FILE_CONTENT
        event_data = {"path": ".some-file.txt", "content": "content"}

        result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result is False
        mock_task_manager.set_cached_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_event_project_structure_complete(self, mock_task_manager):
        """Test handling complete OpenSpec project structure."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {
            "path": "openspec",
            "entries": [
                {"name": "project.md", "type": "file"},
                {"name": "changes", "type": "directory"},
                {"name": "specs", "type": "directory"},
            ],
        }

        with patch.object(task, "request_version_check", new_callable=AsyncMock):
            result = await task.handle_event(EventType.FS_DIRECTORY, event_data)

            assert result is True
            assert task.is_project_enabled() is True
            mock_task_manager.set_cached_data.assert_called_once_with("openspec_project_enabled", True)

    @pytest.mark.asyncio
    async def test_handle_event_project_structure_incomplete(self, mock_task_manager):
        """Test handling incomplete OpenSpec project structure."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {
            "path": "openspec",
            "entries": [
                {"name": "project.md", "type": "file"},
                # Missing changes and specs directories
            ],
        }

        result = await task.handle_event(EventType.FS_DIRECTORY, event_data)

        assert result is True
        assert task.is_project_enabled() is False
        mock_task_manager.set_cached_data.assert_called_once_with("openspec_project_enabled", False)

    @pytest.mark.asyncio
    async def test_handle_event_project_missing_project_md(self, mock_task_manager):
        """Test handling OpenSpec structure missing project.md."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {
            "path": "openspec",
            "entries": [
                {"name": "changes", "type": "directory"},
                {"name": "specs", "type": "directory"},
                # Missing project.md
            ],
        }

        result = await task.handle_event(EventType.FS_DIRECTORY, event_data)

        assert result is True
        assert task.is_project_enabled() is False

    @pytest.mark.asyncio
    async def test_is_project_enabled_returns_none_before_check(self, mock_task_manager):
        """Test that is_project_enabled returns None before project check completes."""
        task = OpenSpecTask(mock_task_manager)
        assert task.is_project_enabled() is None

    @pytest.mark.asyncio
    async def test_get_version_returns_none_initially(self, mock_task_manager):
        """Test that get_version returns None initially."""
        task = OpenSpecTask(mock_task_manager)
        assert task.get_version() is None

    @pytest.mark.asyncio
    async def test_handle_event_version_parsing_valid(self, mock_task_manager):
        """Test parsing valid semantic version."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {"path": ".openspec-version.txt", "content": "openspec version 1.2.3"}

        result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result is True
        assert task.get_version() == "1.2.3"
        mock_task_manager.set_cached_data.assert_called_once_with("openspec_version", "1.2.3")

    @pytest.mark.asyncio
    async def test_handle_event_version_parsing_with_v_prefix(self, mock_task_manager):
        """Test parsing version with v prefix."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {"path": ".openspec-version.txt", "content": "v2.0.1"}

        result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result is True
        assert task.get_version() == "2.0.1"

    @pytest.mark.asyncio
    async def test_handle_event_version_parsing_invalid(self, mock_task_manager):
        """Test parsing invalid version format."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {"path": ".openspec-version.txt", "content": "invalid version"}

        result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result is True
        assert task.get_version() is None

    @pytest.mark.asyncio
    async def test_project_detection_triggers_version_check(self, mock_task_manager):
        """Test that project detection triggers version check."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {
            "path": "openspec",
            "entries": [
                {"name": "project.md", "type": "file"},
                {"name": "changes", "type": "directory"},
                {"name": "specs", "type": "directory"},
            ],
        }

        with patch.object(task, "request_version_check", new_callable=AsyncMock) as mock_request:
            result = await task.handle_event(EventType.FS_DIRECTORY, event_data)

            assert result is True
            assert task.is_project_enabled() is True
            mock_request.assert_called_once()
