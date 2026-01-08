"""Integration tests for workflow state processing flow."""

import logging
from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import Context

from mcp_guide.filesystem.tools import send_file_content
from mcp_guide.task_manager import get_task_manager
from mcp_guide.workflow.tasks import WorkflowMonitorTask


class LogCapture:
    """Capture logs for testing."""

    def __init__(self):
        self.records = []
        self.handler = logging.Handler()
        self.handler.emit = self.records.append

    def __enter__(self):
        # Add handler to all relevant loggers
        loggers = [
            logging.getLogger("mcp_guide.filesystem.tools"),
            logging.getLogger("mcp_guide.task_manager"),
            logging.getLogger("mcp_guide.workflow.tasks"),
            logging.getLogger("mcp_guide.utils.template_context_cache"),
        ]
        for logger in loggers:
            logger.addHandler(self.handler)
            logger.setLevel(logging.DEBUG)
        return self

    def __exit__(self, *args):
        # Remove handler from all loggers
        for logger in logging.getLogger().manager.loggerDict.values():
            if hasattr(logger, "removeHandler"):
                logger.removeHandler(self.handler)

    def get_messages(self, level=None):
        """Get log messages, optionally filtered by level."""
        messages = [record.getMessage() for record in self.records]
        if level:
            messages = [msg for record, msg in zip(self.records, messages) if record.levelno >= level]
        return messages

    def has_warning_or_error(self):
        """Check if any warning or error logs were captured."""
        return any(record.levelno >= logging.WARNING for record in self.records)


@pytest.fixture
def mock_context():
    """Mock MCP context."""
    context = AsyncMock(spec=Context)
    return context


@pytest.fixture
def workflow_content():
    """Sample workflow file content."""
    return """phase: review
issue: project-status/workflow-context
description: All mandatory checks passed - workflow state integration complete
queue:
  - project-status/workflow-templates"""


@pytest.fixture(autouse=True)
def reset_task_manager():
    """Reset TaskManager singleton before each test."""
    from mcp_guide.task_manager.manager import TaskManager

    TaskManager._reset_for_testing()
    yield
    TaskManager._reset_for_testing()


class TestWorkflowIntegration:
    """Test complete workflow state processing integration."""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_file_content_caching(self, mock_context, workflow_content):
        """Test that file content is properly cached."""

        with LogCapture() as logs:
            result = await send_file_content(
                context=mock_context, path=".guide.yaml", content=workflow_content, mtime=1234567890.0, encoding="utf-8"
            )

            assert result.success, f"File caching failed: {result.error}"
            assert result.value["path"] == ".guide.yaml"
            assert "cached" in result.message.lower()

            # Check for expected log messages
            messages = logs.get_messages()
            cache_logs = [msg for msg in messages if "cache" in msg.lower()]
            assert len(cache_logs) > 0, "No caching logs found"

            if logs.has_warning_or_error():
                error_msgs = logs.get_messages(logging.WARNING)
                pytest.fail(f"Unexpected warnings/errors during caching: {error_msgs}")

    @pytest.mark.asyncio
    async def test_task_manager_receives_data(self, mock_context, workflow_content):
        """Test that TaskManager receives file content data."""

        with LogCapture() as logs:
            # Send file content first
            await send_file_content(context=mock_context, path=".guide.yaml", content=workflow_content)

            # Get TaskManager and register a test task
            task_manager = get_task_manager()
            test_task = AsyncMock()
            test_task.process_data = AsyncMock()

            def callback(data_type, data):
                return data.get("path") == ".guide.yaml"

            from mcp_guide.task_manager.interception import FSEventType

            task_manager.register_interest(test_task, FSEventType.FILE_CONTENT, callback)

            # Simulate file content event
            result = await task_manager.handle_agent_data(
                FSEventType.FILE_CONTENT, {"path": ".guide.yaml", "content": workflow_content}
            )

            assert result["status"] == "processed", "TaskManager didn't process the data"
            test_task.process_data.assert_called_once()

            if logs.has_warning_or_error():
                error_msgs = logs.get_messages(logging.WARNING)
                pytest.fail(f"Unexpected warnings/errors in TaskManager: {error_msgs}")

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_workflow_task_updates_cache(self, mock_context, workflow_content):
        """Test that WorkflowMonitorTask correctly updates TaskManager cache."""

        with LogCapture() as logs:
            task_manager = get_task_manager()
            workflow_task = WorkflowMonitorTask(".guide.yaml")

            # Register and process
            def is_workflow_file(data_type, data):
                return data.get("path") == ".guide.yaml"

            from mcp_guide.task_manager.interception import FSEventType

            task_manager.register_interest(workflow_task, FSEventType.FILE_CONTENT, is_workflow_file)

            await task_manager.handle_agent_data(
                FSEventType.FILE_CONTENT, {"path": ".guide.yaml", "content": workflow_content}
            )

            # Verify cache was updated
            cached_workflow = task_manager.get_cached_data("workflow_state")
            assert cached_workflow is not None, "Workflow state not cached"
            assert cached_workflow.phase == "review"
            assert cached_workflow.issue == "project-status/workflow-context"
            assert cached_workflow.description == "All mandatory checks passed - workflow state integration complete"

            if logs.has_warning_or_error():
                error_msgs = logs.get_messages(logging.WARNING)
                pytest.fail(f"Unexpected warnings/errors during cache update: {error_msgs}")
