"""Integration tests for workflow state processing flow."""

import logging
from typing import Any, Generator
from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import Context

from mcp_guide.filesystem.tools import send_file_content
from mcp_guide.task_manager import get_task_manager
from mcp_guide.workflow.tasks import WorkflowMonitorTask


class LogCapture:
    """Capture logs for testing."""

    def __init__(self) -> None:
        self.records: list[logging.LogRecord] = []
        self.handler = logging.Handler()
        self.handler.emit = self.records.append  # type: ignore[assignment]

    def __enter__(self) -> "LogCapture":
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

    def __exit__(self, *args: Any) -> None:
        # Remove handler from all loggers
        for logger in logging.getLogger().manager.loggerDict.values():
            if hasattr(logger, "removeHandler"):
                logger.removeHandler(self.handler)

    def get_messages(self, level: int | None = None) -> list[str]:
        """Get log messages, optionally filtered by level."""
        messages = [record.getMessage() for record in self.records]
        if level:
            messages = [msg for record, msg in zip(self.records, messages) if record.levelno >= level]
        return messages

    def has_warning_or_error(self) -> bool:
        """Check if any warning or error logs were captured."""
        return any(record.levelno >= logging.WARNING for record in self.records)


@pytest.fixture
def mock_context() -> AsyncMock:
    """Mock MCP context."""
    context = AsyncMock(spec=Context)
    return context


@pytest.fixture
def workflow_content() -> str:
    """Sample workflow file content."""
    return """phase: review
issue: project-status/workflow-context
description: All mandatory checks passed - workflow state integration complete
queue:
  - project-status/workflow-templates"""


@pytest.fixture(autouse=True)
def reset_task_manager() -> Generator[None, None, None]:
    """Reset TaskManager singleton before each test."""
    from mcp_guide.task_manager.manager import TaskManager

    TaskManager._reset_for_testing()
    yield
    TaskManager._reset_for_testing()


class TestWorkflowIntegration:
    """Test complete workflow state processing integration."""

    @pytest.mark.asyncio
    async def test_file_content_caching(self, mock_context: AsyncMock, workflow_content: str) -> None:
        """Test that file content is properly cached."""

        with LogCapture() as logs:
            result = await send_file_content(
                context=mock_context, path=".guide.yaml", content=workflow_content, mtime=1234567890.0, encoding="utf-8"
            )

            assert result.success, f"File caching failed: {result.error}"
            if result.value is not None:
                assert result.value["path"] == ".guide.yaml"
            assert result.message is not None and "cached" in result.message.lower()

            # Check for expected log messages
            messages = logs.get_messages()
            cache_logs = [msg for msg in messages if "cache" in msg.lower()]
            assert len(cache_logs) > 0, "No caching logs found"

            if logs.has_warning_or_error():
                error_msgs = logs.get_messages(logging.WARNING)
                pytest.fail(f"Unexpected warnings/errors during caching: {error_msgs}")

    @pytest.mark.asyncio
    async def test_task_manager_receives_data(self, mock_context: AsyncMock, workflow_content: str) -> None:
        """Test that TaskManager receives file content data."""

        with LogCapture() as logs:
            # Send file content first
            await send_file_content(context=mock_context, path=".guide.yaml", content=workflow_content)

            # Get TaskManager and register a test task
            task_manager = get_task_manager()

            # Create a mock subscriber that implements TaskSubscriber protocol
            class MockSubscriber:
                def __init__(self) -> None:
                    self.received_events: list[tuple[Any, dict[str, Any]]] = []

                async def handle_event(self, event_type: Any, data: dict[str, Any]) -> bool:
                    if data.get("path") == ".guide.yaml":
                        self.received_events.append((event_type, data))
                        return True
                    return False

            test_subscriber = MockSubscriber()

            from mcp_guide.task_manager.interception import EventType

            await task_manager.subscribe(test_subscriber, EventType.FS_FILE_CONTENT)

            # Simulate file content event
            result = await task_manager.dispatch_event(
                EventType.FS_FILE_CONTENT, {"path": ".guide.yaml", "content": workflow_content}
            )

            assert result["status"] == "processed", "TaskManager didn't process the data"
            assert len(test_subscriber.received_events) == 1, "Subscriber didn't receive the event"
            event_type, event_data = test_subscriber.received_events[0]
            assert event_type == EventType.FS_FILE_CONTENT
            assert event_data["path"] == ".guide.yaml"

            if logs.has_warning_or_error():
                error_msgs = logs.get_messages(logging.WARNING)
                pytest.fail(f"Unexpected warnings/errors in TaskManager: {error_msgs}")

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_workflow_task_updates_cache(self, mock_context: AsyncMock, workflow_content: str) -> None:
        """Test that WorkflowMonitorTask correctly updates TaskManager cache."""

        with LogCapture() as logs:
            task_manager = get_task_manager()
            workflow_task = WorkflowMonitorTask(".guide.yaml")

            from mcp_guide.task_manager.interception import EventType

            await task_manager.subscribe(workflow_task, EventType.FS_FILE_CONTENT)

            await task_manager.dispatch_event(
                EventType.FS_FILE_CONTENT, {"path": ".guide.yaml", "content": workflow_content}
            )

            # Give the async task time to complete
            import asyncio

            await asyncio.sleep(0.1)

            # Verify cache was updated
            cached_workflow = task_manager.get_cached_data("workflow_state")
            assert cached_workflow is not None, "Workflow state not cached"
            assert cached_workflow.phase == "review"
            assert cached_workflow.issue == "project-status/workflow-context"
            assert cached_workflow.description == "All mandatory checks passed - workflow state integration complete"

            if logs.has_warning_or_error():
                error_msgs = logs.get_messages(logging.WARNING)
                pytest.fail(f"Unexpected warnings/errors during cache update: {error_msgs}")
