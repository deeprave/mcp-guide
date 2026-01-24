"""Tests for OpenSpec CLI detection task."""

import json
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
        """Test that task subscribes to events."""
        task = OpenSpecTask(mock_task_manager)

        assert mock_task_manager.subscribe.call_count == 2

        # First call: TIMER_ONCE and FS_COMMAND with 5s interval
        first_call = mock_task_manager.subscribe.call_args_list[0]
        assert first_call[0][0] == task
        assert first_call[0][1] & EventType.TIMER_ONCE
        assert first_call[0][1] & EventType.FS_COMMAND
        assert first_call[0][2] == 5.0

        # Second call: TIMER for changes monitoring
        second_call = mock_task_manager.subscribe.call_args_list[1]
        assert second_call[0][0] == task
        assert second_call[0][1] & EventType.TIMER
        assert second_call[0][2] == 3600.0  # 60 min interval

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

        with (
            patch("mcp_guide.client_context.openspec_task.render_common_template") as mock_render,
            patch("mcp_guide.utils.flag_utils.get_resolved_flag_value") as mock_flag,
        ):
            mock_render.return_value = "check cli instruction"
            mock_flag.return_value = True  # OpenSpec enabled

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
    async def test_handle_event_cli_not_found_no_project_check(self, mock_task_manager):
        """Test CLI not found does not trigger project check."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {"command": "openspec", "found": False}

        assert task._project_requested is False

        with patch.object(task, "request_project_check", new_callable=AsyncMock) as mock_request:
            result = await task.handle_event(EventType.FS_COMMAND, event_data)

            assert result is True
            assert task.is_available() is False
            mock_task_manager.set_cached_data.assert_called_once_with("openspec_available", False)
            mock_request.assert_not_called()
            assert task._project_requested is False

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
            "path": "openspec/project.md",
            "content": "# OpenSpec Project",
        }

        with (
            patch.object(task, "request_version_check", new_callable=AsyncMock),
            patch.object(task, "request_changes_json", new_callable=AsyncMock),
        ):
            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            assert result is True
            assert task.is_project_enabled() is True
            mock_task_manager.set_cached_data.assert_called_with("openspec_project_enabled", True)

    @pytest.mark.asyncio
    async def test_handle_event_project_structure_incomplete(self, mock_task_manager):
        """Test handling missing OpenSpec project.md file."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {
            "path": "openspec/other.md",
            "content": "# Other file",
        }

        result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result is False
        assert task.is_project_enabled() is None

    @pytest.mark.asyncio
    async def test_handle_event_project_missing_project_md(self, mock_task_manager):
        """Test that project is not enabled without project.md."""
        task = OpenSpecTask(mock_task_manager)

        # Simulate no project.md file received
        assert task.is_project_enabled() is None

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
        mock_task_manager.set_cached_data.assert_called_with("openspec_version", None)

    @pytest.mark.asyncio
    async def test_project_detection_triggers_version_check(self, mock_task_manager):
        """Test that project detection triggers version and changes check."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {
            "path": "openspec/project.md",
            "content": "# OpenSpec Project",
        }

        with (
            patch.object(task, "request_version_check", new_callable=AsyncMock) as mock_version,
            patch.object(task, "request_changes_json", new_callable=AsyncMock) as mock_changes,
        ):
            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            assert result is True
            assert task.is_project_enabled() is True
            mock_version.assert_called_once()
            mock_changes.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_event_changes_json_caches_data(self, mock_task_manager):
        """Test handling changes JSON caches the data."""
        task = OpenSpecTask(mock_task_manager)

        changes_data = [
            {"name": "change-1", "status": "in-progress", "completedTasks": 0, "totalTasks": 5},
            {"name": "change-2", "status": "complete", "completedTasks": 10, "totalTasks": 10},
        ]
        event_data = {
            "path": ".openspec-changes.json",
            "content": json.dumps({"changes": changes_data}),
        }

        with patch("time.time", return_value=1234567890.0):
            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            assert result is True
            cached = task.get_changes()
            assert len(cached) == 2
            # Verify filter flags were added
            assert cached[0]["is_draft"] is False
            assert cached[0]["is_done"] is False
            assert cached[0]["is_in_progress"] is True  # Has tasks but not done
            assert cached[1]["is_done"] is True
            mock_task_manager.set_cached_data.assert_called()

    @pytest.mark.asyncio
    async def test_get_changes_returns_none_when_no_cache(self, mock_task_manager):
        """Test get_changes returns None when cache is empty."""
        task = OpenSpecTask(mock_task_manager)
        assert task.get_changes() is None

    @pytest.mark.asyncio
    async def test_is_cache_valid_returns_false_when_no_cache(self, mock_task_manager):
        """Test is_cache_valid returns False when cache is empty."""
        task = OpenSpecTask(mock_task_manager)
        assert task.is_cache_valid() is False

    @pytest.mark.asyncio
    async def test_is_cache_valid_returns_true_when_fresh(self, mock_task_manager):
        """Test is_cache_valid returns True when cache is fresh."""
        task = OpenSpecTask(mock_task_manager)
        task._changes_cache = [{"name": "test"}]

        with patch("time.time", return_value=1000.0):
            task._changes_timestamp = 900.0  # 100 seconds ago
            assert task.is_cache_valid() is True

    @pytest.mark.asyncio
    async def test_is_cache_valid_returns_false_when_stale(self, mock_task_manager):
        """Test is_cache_valid returns False when cache is stale."""
        task = OpenSpecTask(mock_task_manager)
        task._changes_cache = [{"name": "test"}]

        with patch("time.time", return_value=5000.0):
            task._changes_timestamp = 100.0  # 4900 seconds ago (> 3600 TTL)
            assert task.is_cache_valid() is False

    @pytest.mark.asyncio
    async def test_timer_event_calls_changes_reminder_when_enabled(self, mock_task_manager):
        """Test TIMER event with 3600s interval calls changes reminder when project enabled."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True
        task._project_enabled = True

        with patch.object(task, "_handle_changes_reminder", new_callable=AsyncMock) as mock_reminder:
            result = await task.handle_event(EventType.TIMER, {"interval": 3600.0, "startDelay": 20.0})

            assert result is True
            mock_reminder.assert_called_once()

    @pytest.mark.asyncio
    async def test_timer_event_skips_reminder_before_start_delay(self, mock_task_manager):
        """Test TIMER event skips changes reminder before start delay."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True
        task._project_enabled = True

        with patch.object(task, "_handle_changes_reminder", new_callable=AsyncMock) as mock_reminder:
            result = await task.handle_event(EventType.TIMER, {"interval": 3600.0, "startDelay": 10.0})

            assert result is True
            mock_reminder.assert_not_called()

    @pytest.mark.asyncio
    async def test_timer_event_skips_reminder_when_disabled(self, mock_task_manager):
        """Test TIMER event skips changes reminder when project not enabled."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True
        task._project_enabled = False

        with patch.object(task, "request_changes_json", new_callable=AsyncMock) as mock_request:
            result = await task.handle_event(EventType.TIMER, {"interval": 3600.0, "startDelay": 20.0})

            assert result is True
            mock_request.assert_not_called()


class TestOpenSpecResponseFormatting:
    """Test OpenSpec response formatting."""

    @pytest.fixture
    def mock_task_manager(self):
        """Create mock task manager."""
        manager = MagicMock()
        manager.queue_instruction = AsyncMock()
        manager.set_cached_data = MagicMock()
        manager.get_cached_data = MagicMock(return_value=None)
        return manager

    @pytest.mark.asyncio
    async def test_format_status_response_complete(self, mock_task_manager):
        """Test formatting complete status response."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True

        status_data = {
            "changeName": "test-change",
            "schemaName": "spec-driven",
            "isComplete": True,
            "artifacts": [
                {"id": "proposal", "outputPath": "proposal.md", "status": "done"},
                {"id": "tasks", "outputPath": "tasks.md", "status": "done"},
            ],
        }

        event_data = {"path": ".openspec-status.json", "content": json.dumps(status_data)}

        with patch("mcp_guide.client_context.openspec_task.render_common_template") as mock_render:
            mock_render.return_value = "## OpenSpec Status: test-change\n\n**Status:** ✅ Complete"

            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            assert result is True
            assert mock_task_manager.queue_instruction.call_count == 1
            mock_render.assert_called_once_with("_commands/openspec/_status-format", extra_context=status_data)

    @pytest.mark.asyncio
    async def test_format_status_response_in_progress(self, mock_task_manager):
        """Test formatting in-progress status response."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True

        status_data = {
            "changeName": "test-change",
            "schemaName": "spec-driven",
            "isComplete": False,
            "artifacts": [{"id": "proposal", "outputPath": "proposal.md", "status": "done"}],
        }

        event_data = {"path": ".openspec-status.json", "content": json.dumps(status_data)}

        with patch("mcp_guide.client_context.openspec_task.render_common_template") as mock_render:
            mock_render.return_value = "## OpenSpec Status: test-change\n\n**Status:** ⏳ In Progress"

            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            assert result is True
            mock_render.assert_called_once_with("_commands/openspec/_status-format", extra_context=status_data)

    @pytest.mark.asyncio
    async def test_format_changes_list_response(self, mock_task_manager):
        """Test formatting changes list response including sorting and derived fields."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True

        changes_data = {
            "changes": [
                {
                    "name": "change-1",
                    "status": "complete",
                    "completedTasks": 10,
                    "totalTasks": 10,
                    "lastModified": "2024-01-01T10:00:00Z",
                },
                {
                    "name": "change-2",
                    "status": "in-progress",
                    "completedTasks": 0,
                    "totalTasks": 0,
                    "lastModified": "2024-01-02T12:00:00Z",
                },
            ]
        }

        event_data = {"path": ".openspec-changes.json", "content": json.dumps(changes_data)}

        result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result is True
        # Verify changes were cached with filter flags
        assert task.get_changes() is not None
        assert len(task.get_changes()) == 2
        # Verify filter flags were added
        assert task.get_changes()[0]["is_done"] is True
        assert task.get_changes()[1]["is_draft"] is True

    @pytest.mark.asyncio
    async def test_format_changes_list_empty(self, mock_task_manager):
        """Test caching empty changes list."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True

        changes_data = {"changes": []}

        event_data = {"path": ".openspec-changes.json", "content": json.dumps(changes_data)}

        result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result is True
        # Verify empty cache
        assert task.get_changes() == []

    @pytest.mark.asyncio
    async def test_format_show_response(self, mock_task_manager):
        """Test formatting show response."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True

        show_data = {
            "changeName": "test-change",
            "schemaName": "spec-driven",
            "description": "Test description",
            "artifacts": [{"id": "proposal", "outputPath": "proposal.md", "status": "done"}],
        }

        event_data = {"path": ".openspec-show.json", "content": json.dumps(show_data)}

        with patch("mcp_guide.client_context.openspec_task.render_common_template") as mock_render:
            mock_render.return_value = "## OpenSpec Change: test-change"

            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            assert result is True
            mock_render.assert_called_once_with("_commands/openspec/_show-format", extra_context=show_data)

    @pytest.mark.asyncio
    async def test_format_error_response(self, mock_task_manager):
        """Test formatting error response."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True

        error_data = {
            "error": "Missing required option --change",
            "message": "Please specify a change name",
            "available_changes": ["change-1", "change-2"],
        }

        event_data = {"path": ".openspec-status.json", "content": json.dumps(error_data)}

        with patch("mcp_guide.client_context.openspec_task.render_common_template") as mock_render:
            mock_render.return_value = "## OpenSpec Error\n\nMissing required option --change"

            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            assert result is True
            mock_render.assert_called_once_with("_commands/openspec/_error-format", extra_context=error_data)

    @pytest.mark.asyncio
    async def test_format_malformed_json(self, mock_task_manager):
        """Test handling malformed JSON."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True

        event_data = {"path": ".openspec-status.json", "content": "not valid json"}

        result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result is False  # Should return False for non-JSON content
        assert mock_task_manager.queue_instruction.call_count == 0
