"""Tests for WorkflowMonitorTask acknowledgement tracking."""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_guide.render.content import RenderedContent
from mcp_guide.render.frontmatter import Frontmatter
from mcp_guide.task_manager.interception import EventType
from mcp_guide.task_manager.manager import TaskManager
from mcp_guide.workflow.tasks import WorkflowMonitorTask


def make_rendered_content(content: str) -> RenderedContent:
    """Helper to create RenderedContent for mocking."""
    from pathlib import Path

    return RenderedContent(
        content=content,
        frontmatter=Frontmatter({}),
        template_path=Path("test.mustache"),
        template_name="test",
        frontmatter_length=0,
        content_length=len(content),
    )


@pytest.fixture(autouse=True)
def reset_task_manager():
    """Reset TaskManager singleton before each test."""
    TaskManager._instance = None
    yield
    TaskManager._instance = None


class TestWorkflowMonitorTaskAcknowledgement:
    """Test WorkflowMonitorTask acknowledgement tracking."""

    @pytest.mark.anyio
    async def test_setup_request_stores_instruction_id(self):
        """Test that setup request stores instruction ID."""
        manager = TaskManager()
        manager._resolved_flags = {"workflow": True}
        task = WorkflowMonitorTask()
        task.task_manager = manager

        with patch("mcp_guide.workflow.tasks.render_workflow_template", new_callable=AsyncMock) as mock_render:
            mock_render.return_value = make_rendered_content("setup content")
            await task.on_init()

        assert task._setup_instruction_id is not None
        assert task._setup_instruction_id in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_workflow_content_acknowledges_setup(self):
        """Test that workflow content response acknowledges setup instruction."""
        manager = TaskManager()
        manager._resolved_flags = {"workflow": True}
        task = WorkflowMonitorTask()
        task.task_manager = manager

        with patch("mcp_guide.workflow.tasks.render_workflow_template", new_callable=AsyncMock) as mock_render:
            mock_render.return_value = make_rendered_content("setup content")
            await task.on_init()

        instruction_id = task._setup_instruction_id

        # Simulate workflow file response
        await task.handle_event(
            EventType.FS_FILE_CONTENT, {"path": ".guide.yaml", "content": "Phase: discussion\nIssue: test"}
        )

        assert instruction_id not in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_reminder_request_stores_instruction_id(self):
        """Test that reminder request stores instruction ID."""
        manager = TaskManager()
        task = WorkflowMonitorTask()
        task.task_manager = manager

        with patch("mcp_guide.workflow.tasks.render_workflow_template", new_callable=AsyncMock) as mock_render:
            mock_render.return_value = make_rendered_content("reminder content")
            await task._handle_monitoring_reminder()

        assert task._reminder_instruction_id is not None
        assert task._reminder_instruction_id in manager._tracked_instructions

    @pytest.mark.anyio
    async def test_workflow_content_acknowledges_reminder(self):
        """Test that workflow content response acknowledges reminder instruction."""
        manager = TaskManager()
        task = WorkflowMonitorTask()
        task.task_manager = manager

        with patch("mcp_guide.workflow.tasks.render_workflow_template", new_callable=AsyncMock) as mock_render:
            mock_render.return_value = make_rendered_content("reminder content")
            await task._handle_monitoring_reminder()

        instruction_id = task._reminder_instruction_id

        # Simulate workflow file response
        await task.handle_event(
            EventType.FS_FILE_CONTENT, {"path": ".guide.yaml", "content": "Phase: discussion\nIssue: test"}
        )

        assert instruction_id not in manager._tracked_instructions
