"""Tests for workflow-specific task implementations."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.cache import TemplateContextCache
from mcp_guide.render.content import RenderedContent
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.frontmatter import Frontmatter
from mcp_guide.render.template import render_template
from mcp_guide.task_manager import EventType
from mcp_guide.task_manager.manager import TaskManager, aggregate_event_results
from mcp_guide.workflow.parser import parse_workflow_state
from mcp_guide.workflow.tasks import WorkflowMonitorTask


def make_rendered_content(content: str, instruction: str = "Follow the workflow format") -> RenderedContent:
    """Build workflow content with its agent-instruction frontmatter."""
    return RenderedContent(
        content=content,
        content_length=len(content),
        frontmatter=Frontmatter({"type": "agent/instruction", "instruction": instruction}),
        frontmatter_length=0,
        template_path=Path("state-format.mustache"),
        template_name="state-format.mustache",
    )


def _manager() -> TaskManager:
    """Create a manager with the session ownership required for cache updates."""
    return TaskManager(session=Mock(template_cache=Mock()))


class TestWorkflowMonitorTask:
    """Test WorkflowMonitorTask functionality."""

    @pytest.fixture
    def monitor_task(self):
        return WorkflowMonitorTask(".guide.yaml", task_manager=_manager())

    def test_workflow_monitor_task_creation(self, monitor_task) -> None:
        """Test WorkflowMonitorTask can be created."""
        assert monitor_task.get_name() == "WorkflowMonitorTask"

    @pytest.mark.anyio
    async def test_workflow_monitor_task_handles_events(self, monitor_task) -> None:
        """Test WorkflowMonitorTask handles events correctly."""
        # Test file content event handling
        result = await monitor_task.handle_event(
            EventType.FS_FILE_CONTENT, {"path": ".guide.yaml", "content": "phase: test\nissue: test-issue"}
        )
        assert result.result is True

    @pytest.mark.anyio
    async def test_workflow_monitor_task_ignores_unrelated_events(self, monitor_task) -> None:
        """Test WorkflowMonitorTask ignores unrelated events and leaves state unchanged."""
        import copy

        # Capture initial state before dispatching any events
        exclude = {"task_manager"}
        initial_filtered = {k: v for k, v in monitor_task.__dict__.items() if k not in exclude}

        # Non-matching file content event (different path)
        result_file_content = await monitor_task.handle_event(
            EventType.FS_FILE_CONTENT,
            {"path": "unrelated/config.yaml", "content": "phase: other\nissue: other-issue"},
        )
        assert result_file_content is None

        # Directory event should also be ignored
        result_directory = await monitor_task.handle_event(
            EventType.FS_DIRECTORY,
            {"path": ".guide", "action": "modified"},
        )
        assert result_directory is None

        # Ensure state has not changed after handling unrelated events
        # Exclude task_manager (contains asyncio.Task, not picklable and not relevant state)
        final_filtered = {k: v for k, v in monitor_task.__dict__.items() if k not in exclude}
        assert copy.deepcopy(final_filtered) == copy.deepcopy(initial_filtered)

    @pytest.mark.anyio
    async def test_unchanged_workflow_content_uses_state_format_response(self, monitor_task) -> None:
        """A parsed unchanged state responds with rendered format guidance."""
        await TaskManager._reset_for_testing()
        manager = _manager()
        session = Mock()
        monitor_task.task_manager = manager
        monitor_task._session = session
        content = "phase: discussion\nissue: add-workflow-format\n"
        manager.set_cached_data("workflow_state", parse_workflow_state(content))
        rendered = make_rendered_content("# Workflow State File Format")

        with patch("mcp_guide.workflow.tasks.render_workflow_template", new_callable=AsyncMock) as render:
            render.return_value = rendered
            event_result = await monitor_task.handle_event(
                EventType.FS_FILE_CONTENT, {"path": ".guide.yaml", "content": content}
            )

        render.assert_awaited_once_with(session, "state-format")
        assert event_result is not None
        assert event_result.rendered_content == rendered
        assert manager.get_cached_data("workflow_change_content") is None
        result = aggregate_event_results([event_result])
        assert result.value == rendered.content
        assert result.instruction == rendered.instruction
        assert result.disposition == "agent/instruction"

    @pytest.mark.anyio
    async def test_unavailable_state_format_retains_file_content_response(self, monitor_task) -> None:
        """An unavailable fallback leaves the ordinary file-content response intact."""
        await TaskManager._reset_for_testing()
        manager = _manager()
        session = Mock()
        monitor_task.task_manager = manager
        monitor_task._session = session
        content = "phase: discussion\nissue: add-workflow-format\n"
        manager.set_cached_data("workflow_state", parse_workflow_state(content))

        with patch("mcp_guide.workflow.tasks.render_workflow_template", new_callable=AsyncMock) as render:
            render.return_value = None
            event_result = await monitor_task.handle_event(
                EventType.FS_FILE_CONTENT, {"path": ".guide.yaml", "content": content}
            )

        render.assert_awaited_once_with(session, "state-format")
        assert event_result is not None
        assert event_result.rendered_content is None
        assert manager.get_cached_data("workflow_change_content") is None

    @pytest.mark.anyio
    async def test_semantic_change_response_takes_precedence_over_state_format(self, monitor_task) -> None:
        """A semantic change never requests or replaces its response with format guidance."""
        await TaskManager._reset_for_testing()
        manager = _manager()
        session = Mock()
        monitor_task.task_manager = manager
        monitor_task._session = session
        manager.set_cached_data("workflow_state", parse_workflow_state("phase: discussion\n"))
        semantic_response = make_rendered_content("# Planning")

        with patch("mcp_guide.workflow.tasks.render_workflow_template", new_callable=AsyncMock) as render:
            render.return_value = semantic_response
            event_result = await monitor_task.handle_event(
                EventType.FS_FILE_CONTENT, {"path": ".guide.yaml", "content": "phase: planning\n"}
            )

        assert render.await_count == 1
        assert event_result is not None
        assert event_result.rendered_content == semantic_response
        assert manager.get_cached_data("workflow_change_content") is None
        result = aggregate_event_results([event_result])
        assert result.value == semantic_response.content

    @pytest.mark.anyio
    async def test_state_format_template_provides_strict_yaml_file_guidance(self) -> None:
        """The rendered state-format template explains the complete YAML contract."""
        template_path = Path("src/mcp_guide/templates/_workflow/state-format.mustache")
        file_info = FileInfo(
            path=template_path,
            size=template_path.stat().st_size,
            content_size=template_path.stat().st_size,
            mtime=datetime.fromtimestamp(template_path.stat().st_mtime),
            name=template_path.name,
        )

        session = Mock()
        session.agent_info = None
        session.client_params = None
        session.get_project = AsyncMock(side_effect=ValueError("no project"))
        session.runtime.feature_flags.return_value.list = AsyncMock(return_value={})
        session.project_flags.return_value.list = AsyncMock(return_value={"workflow": True})
        session.task_manager.get_cached_data.return_value = None
        session.task_manager.get_task_statistics.return_value = {}

        session.template_cache = TemplateContextCache(session)

        rendered = await render_template(
            session,
            file_info=file_info,
            base_dir=template_path.parent,
            project_flags={"workflow": True},
            context=TemplateContext({"workflow": {"file": ".guide.yaml"}}),
        )

        assert rendered is not None
        assert "# Workflow State File Format" in rendered.content
        assert "strictly valid YAML" in rendered.content
        assert "lowercase keys" in rendered.content
        assert "Optional lines may be omitted" in rendered.content
        assert "description: <optional-description>" in rendered.content
        assert "`send_file_content` MCP tool" in rendered.content
