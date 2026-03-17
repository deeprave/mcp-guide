"""Tests for OpenSpec CLI detection task."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_guide.openspec.task import OpenSpecTask
from mcp_guide.render.content import RenderedContent
from mcp_guide.render.frontmatter import Frontmatter
from mcp_guide.task_manager import EventType


def make_rendered_content(content: str, instruction: str | None = None) -> RenderedContent:
    """Helper to create RenderedContent for mocking."""
    return RenderedContent(
        content=content,
        frontmatter=Frontmatter({"instruction": instruction} if instruction else {}),
        template_path=Path("test.mustache"),
        template_name="test",
        frontmatter_length=0,
        content_length=len(content),
    )


@pytest.fixture
def mock_task_manager():
    """Create a mock task manager."""
    manager = MagicMock()
    manager.subscribe = MagicMock()  # Synchronous
    manager.unsubscribe = AsyncMock()
    manager.queue_instruction = AsyncMock()
    manager.queue_instruction_with_ack = AsyncMock(return_value="test-id")
    manager.acknowledge_instruction = AsyncMock()
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

    @pytest.mark.anyio
    async def test_init_subscribes_to_events(self, mock_task_manager):
        """Test that task subscribes to events."""
        task = OpenSpecTask(mock_task_manager)

        assert mock_task_manager.subscribe.call_count == 1

        # Single call with all event types
        call = mock_task_manager.subscribe.call_args_list[0]
        assert call[0][0] == task
        assert call[0][1] & EventType.FS_COMMAND
        assert call[0][1] & EventType.FS_FILE_CONTENT
        assert call[0][1] & EventType.TIMER
        assert call[0][2] == 3600.0  # 60 min interval

    @pytest.mark.anyio
    async def test_get_name(self, mock_task_manager):
        """Test task name."""
        task = OpenSpecTask(mock_task_manager)
        assert task.get_name() == "OpenSpecTask"

        task = OpenSpecTask(mock_task_manager)

        with patch("mcp_guide.feature_flags.utils.get_resolved_flag_value", new_callable=AsyncMock) as mock_get_flag:
            mock_get_flag.return_value = True

            await task.on_tool()

            mock_task_manager.unsubscribe.assert_not_called()

    @pytest.mark.anyio
    async def test_handle_event_cli_found(self, mock_task_manager):
        """Test handling CLI found response."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {"command": "openspec", "path": "/usr/local/bin/openspec", "found": True}

        with patch.object(task, "request_version_check", new_callable=AsyncMock) as mock_request:
            result = await task.handle_event(EventType.FS_COMMAND, event_data)

            assert result.result is True
            assert task.is_available() is True
            mock_task_manager.set_cached_data.assert_called_once_with("openspec_available", True)
            mock_request.assert_called_once()

    @pytest.mark.anyio
    async def test_handle_event_cli_not_found_no_project_check(self, mock_task_manager):
        """Test CLI not found does not trigger project check."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {"command": "openspec", "found": False}

        assert task._project_requested is False

        with patch.object(task, "request_project_check", new_callable=AsyncMock) as mock_request:
            result = await task.handle_event(EventType.FS_COMMAND, event_data)

            assert result.result is True
            assert task.is_available() is False
            mock_task_manager.set_cached_data.assert_called_once_with("openspec_available", False)
            mock_request.assert_not_called()
            assert task._project_requested is False

    @pytest.mark.anyio
    async def test_handle_event_cli_not_found(self, mock_task_manager):
        """Test handling CLI not found response."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {"command": "openspec", "path": None, "found": False}

        result = await task.handle_event(EventType.FS_COMMAND, event_data)

        assert result.result is True
        assert task.is_available() is False
        mock_task_manager.set_cached_data.assert_called_once_with("openspec_available", False)

    @pytest.mark.anyio
    async def test_is_available_returns_none_before_check(self, mock_task_manager):
        """Test that is_available returns None before CLI check completes."""
        task = OpenSpecTask(mock_task_manager)
        assert task.is_available() is None

    @pytest.mark.anyio
    async def test_handle_event_ignores_unsubscribed_events(self, mock_task_manager):
        """Test that task ignores events it doesn't subscribe to."""
        task = OpenSpecTask(mock_task_manager)

        # Task only subscribes to TIMER_ONCE, FS_COMMAND, and FS_DIRECTORY, not FS_FILE_CONTENT
        event_data = {"path": ".some-file.txt", "content": "content"}

        result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result is None
        mock_task_manager.set_cached_data.assert_not_called()

    @pytest.mark.anyio
    async def test_handle_event_non_openspec_file(self, mock_task_manager):
        """Test handling non-OpenSpec files."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {
            "path": "openspec/other.md",
            "content": "# Other file",
        }

        result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result is None
        assert task.is_project_enabled() is None

    @pytest.mark.anyio
    async def test_handle_event_project_missing_project_md(self, mock_task_manager):
        """Test that project is not enabled without project.md."""
        task = OpenSpecTask(mock_task_manager)

        # Simulate no project.md file received
        assert task.is_project_enabled() is None

    @pytest.mark.anyio
    async def test_is_project_enabled_returns_none_before_check(self, mock_task_manager):
        """Test that is_project_enabled returns None before project check completes."""
        task = OpenSpecTask(mock_task_manager)
        assert task.is_project_enabled() is None

    @pytest.mark.anyio
    async def test_get_version_returns_none_initially(self, mock_task_manager):
        """Test that get_version returns None initially."""
        task = OpenSpecTask(mock_task_manager)
        assert task.get_version() is None

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "content,expected_version",
        [
            ("openspec version 1.2.3", "1.2.3"),
            ("v2.0.1", "2.0.1"),
            ("invalid version", None),
        ],
    )
    async def test_handle_event_version_parsing(self, content: str, expected_version, mock_task_manager):
        """Test parsing various version formats."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {"path": ".openspec-version.txt", "content": content}

        result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result.result is True
        assert task.get_version() == expected_version
        if expected_version == "1.2.3":
            mock_task_manager.set_cached_data.assert_called_once_with("openspec_version", expected_version)
        else:
            mock_task_manager.set_cached_data.assert_called_with("openspec_version", expected_version)

    @pytest.mark.anyio
    async def test_version_comparison(self, mock_task_manager):
        """Test semantic version comparison."""
        task = OpenSpecTask(mock_task_manager)

        # Set version
        task._version = "1.10.2"

        # Test various comparisons
        assert task.meets_minimum_version("1.9.6") is True
        assert task.meets_minimum_version("1.10.2") is True
        assert task.meets_minimum_version("1.10.3") is False
        assert task.meets_minimum_version("2.0.0") is False

        # Test with v prefix
        assert task.meets_minimum_version("v1.9.6") is True

        # Test with no version set
        task._version = None
        assert task.meets_minimum_version("1.0.0") is False

    @pytest.mark.anyio
    async def test_version_persistence(self, mock_task_manager):
        """Test that version is stored in project config."""
        task = OpenSpecTask(mock_task_manager)

        event_data = {
            "path": ".openspec-version.txt",
            "content": "openspec version 1.2.3",
        }

        with (
            patch("mcp_guide.session.get_session") as mock_session,
            patch.object(task, "request_project_check", new_callable=AsyncMock) as mock_request_project,
        ):
            mock_project = MagicMock()
            mock_project.openspec_version = None
            mock_project.openspec_validated = False  # Required for request_project_check to be called
            mock_session_instance = AsyncMock()
            mock_session_instance.get_project = AsyncMock(return_value=mock_project)
            mock_session_instance.update_config = AsyncMock()
            mock_session.return_value = mock_session_instance

            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result.result is True
        assert task.get_version() == "1.2.3"
        assert task._version_this_session == "1.2.3"
        mock_session_instance.update_config.assert_called_once()
        mock_request_project.assert_called_once()

    @pytest.mark.anyio
    async def test_handle_event_changes_json_caches_data(self, mock_task_manager):
        """Test handling changes JSON caches the data."""
        task = OpenSpecTask(mock_task_manager)

        changes_data = [
            {
                "name": "change-1",
                "status": "in-progress",
                "completedTasks": 0,
                "totalTasks": 5,
                "lastModified": "2024-01-01T10:00:00Z",
            },
            {
                "name": "change-2",
                "status": "complete",
                "completedTasks": 10,
                "totalTasks": 10,
                "lastModified": "2024-01-02T12:00:00Z",
            },
        ]
        event_data = {
            "path": ".openspec-changes.json",
            "content": json.dumps({"changes": changes_data}),
        }

        with (
            patch("time.time", return_value=1234567890.0),
            patch("mcp_guide.openspec.task.render_openspec_template") as mock_render,
        ):
            mock_render.return_value = make_rendered_content("## OpenSpec Changes\n...")
            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            # Now returns EventResult
            from mcp_guide.task_manager.manager import EventResult

            assert isinstance(result, EventResult)
            assert result.result is True

            cached = task.get_changes()
            # Returns grouped dict now
            assert "in_progress" in cached
            assert "complete" in cached
            assert len(cached["in_progress"]) == 1
            assert len(cached["complete"]) == 1
            mock_task_manager.set_cached_data.assert_called()

    @pytest.mark.anyio
    async def test_get_changes_returns_none_when_no_cache(self, mock_task_manager):
        """Test get_changes returns None when cache is empty."""
        task = OpenSpecTask(mock_task_manager)
        assert task.get_changes() is None

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "scenario,has_cache,current_time,timestamp,expected",
        [
            ("no_cache", False, None, None, False),
            ("fresh", True, 1000.0, 900.0, True),
            ("stale", True, 5000.0, 100.0, False),
        ],
    )
    async def test_is_cache_valid(
        self, scenario: str, has_cache: bool, current_time, timestamp, expected: bool, mock_task_manager
    ):
        """Test cache validity under various conditions."""
        task = OpenSpecTask(mock_task_manager)

        if has_cache:
            task._changes_cache = [{"name": "test"}]
            with patch("time.time", return_value=current_time):
                task._changes_timestamp = timestamp
                assert task.is_cache_valid() is expected
        else:
            assert task.is_cache_valid() is expected

    @pytest.mark.anyio
    async def test_timer_event_calls_changes_reminder_when_enabled(self, mock_task_manager):
        """Test TIMER event with 3600s interval calls changes reminder when project enabled."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True
        task._project_enabled = True
        task._changes_timer_started = True  # Skip first-fire check

        with patch.object(task, "_handle_changes_reminder", new_callable=AsyncMock) as mock_reminder:
            result = await task.handle_event(EventType.TIMER, {"interval": 3600.0})

            assert result.result is True
            mock_reminder.assert_called_once()

    @pytest.mark.anyio
    async def test_timer_event_triggers_reminder(self, mock_task_manager):
        """Test TIMER event triggers changes reminder."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True
        task._project_enabled = True

        with patch.object(task, "_handle_changes_reminder", new_callable=AsyncMock) as mock_reminder:
            # Timer event should trigger reminder
            result = await task.handle_event(EventType.TIMER, {"interval": 3600.0})

            assert result.result is True
            mock_reminder.assert_called_once()

    @pytest.mark.anyio
    async def test_timer_event_requests_changes_when_cache_stale(self, mock_task_manager):
        """Test TIMER event invalidates cache when stale."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True
        task._changes_cache = []  # Has cache
        task._changes_timestamp = 0.0  # Stale timestamp

        result = await task.handle_event(EventType.TIMER, {"interval": 3600.0})

        assert result.result is True
        assert task._changes_timestamp is None  # Cache invalidated

    @pytest.mark.anyio
    async def test_timer_event_skips_invalidation_when_cache_valid(self, mock_task_manager):
        """Test TIMER event does not invalidate cache when still valid."""
        import time

        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True
        task._changes_cache = [{"id": "test-change"}]
        initial_timestamp = time.time()
        task._changes_timestamp = initial_timestamp  # Fresh cache

        result = await task.handle_event(EventType.TIMER, {"interval": 3600.0})

        assert result.result is True
        assert task._changes_timestamp == initial_timestamp  # Cache not invalidated


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

    @pytest.mark.anyio
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

        with patch("mcp_guide.openspec.task.render_openspec_template") as mock_render:
            mock_render.return_value = make_rendered_content(
                "## OpenSpec Status: test-change\n\n**Status:** ✅ Complete"
            )

            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            assert result.result is True
            assert result.rendered_content is not None
            # Check that render was called with TemplateContext
            call_args = mock_render.call_args
            assert call_args[0][0] == "_status-format"
            assert "extra_context" in call_args[1]

    @pytest.mark.anyio
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

        with patch("mcp_guide.openspec.task.render_openspec_template") as mock_render:
            mock_render.return_value = make_rendered_content(
                "## OpenSpec Status: test-change\n\n**Status:** ⏳ In Progress"
            )

            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            assert result.result is True
            # Check that render was called with TemplateContext
            call_args = mock_render.call_args
            assert call_args[0][0] == "_status-format"
            assert "extra_context" in call_args[1]

    @pytest.mark.anyio
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

        with patch("mcp_guide.openspec.task.render_openspec_template") as mock_render:
            mock_render.return_value = make_rendered_content("## OpenSpec Changes\n...")
            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            from mcp_guide.task_manager.manager import EventResult

            assert isinstance(result, EventResult)
            assert result.result is True

            # Verify changes were cached and grouped
            cached = task.get_changes()
            assert cached is not None
            assert "complete" in cached
            assert "in_progress" in cached
            assert len(cached["complete"]) == 1
            assert len(cached["in_progress"]) == 1

    @pytest.mark.anyio
    async def test_format_changes_list_empty(self, mock_task_manager):
        """Test caching empty changes list."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True

        changes_data = {"changes": []}

        event_data = {"path": ".openspec-changes.json", "content": json.dumps(changes_data)}

        with patch("mcp_guide.openspec.task.render_openspec_template") as mock_render:
            mock_render.return_value = make_rendered_content("## OpenSpec Changes\n...")
            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            from mcp_guide.task_manager.manager import EventResult

            assert isinstance(result, EventResult)
            assert result.result is True

            # Verify empty cache returns empty groups
            cached = task.get_changes()
            assert cached == {"in_progress": [], "draft": [], "complete": []}

    @pytest.mark.anyio
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

        with patch("mcp_guide.openspec.task.render_openspec_template") as mock_render:
            mock_render.return_value = make_rendered_content("## OpenSpec Change: test-change")

            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            assert result.result is True
            # Check that render was called with TemplateContext
            call_args = mock_render.call_args
            assert call_args[0][0] == "_show-format"
            assert "extra_context" in call_args[1]

    @pytest.mark.anyio
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

        with patch("mcp_guide.openspec.task.render_openspec_template") as mock_render:
            mock_render.return_value = make_rendered_content("## OpenSpec Error\n\nMissing required option --change")

            result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

            assert result.result is False  # Errors return False
            assert result.rendered_content is not None
            # Check that render was called with TemplateContext wrapping the data
            call_args = mock_render.call_args
            assert call_args[0][0] == "_error-format"
            assert "extra_context" in call_args[1]
            # Verify the context contains the expected data
            context = call_args[1]["extra_context"]
            assert context["error"] == error_data["error"]
            assert context["message"] == error_data["message"]

    @pytest.mark.anyio
    async def test_format_malformed_json(self, mock_task_manager):
        """Test handling malformed JSON."""
        task = OpenSpecTask(mock_task_manager)
        task._flag_checked = True

        event_data = {"path": ".openspec-status.json", "content": "not valid json"}

        result = await task.handle_event(EventType.FS_FILE_CONTENT, event_data)

        assert result is None  # Should return False for non-JSON content
        assert mock_task_manager.queue_instruction.call_count == 0
