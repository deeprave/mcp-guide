"""Test tool decorator integration with TaskManager."""

from unittest.mock import MagicMock

from mcp_core.result import Result
from mcp_core.tool_decorator import _process_tool_result, set_task_manager
from mcp_guide.task_manager import TaskManager


class TestToolDecoratorIntegration:
    """Test TaskManager integration with tool decorator."""

    async def test_process_tool_result_no_task_manager(self):
        """Test result processing without TaskManager."""
        set_task_manager(None)
        result = Result.ok("test data")

        processed = await _process_tool_result(result, "test_tool")

        # Should return JSON string without TaskManager processing
        assert isinstance(processed, str)
        assert "test data" in processed

    async def test_process_tool_result_with_task_manager(self):
        """Test result processing with TaskManager."""
        task_manager = TaskManager()
        task_manager.queue_instruction("Please check status")
        set_task_manager(task_manager)

        result = Result.ok("test data")
        processed = await _process_tool_result(result, "test_tool")

        # Should return JSON string with additional instruction
        assert isinstance(processed, str)
        assert "test data" in processed
        assert "Please check status" in processed

    async def test_process_tool_result_string_passthrough(self):
        """Test that string results pass through unchanged."""
        set_task_manager(TaskManager())

        json_string = '{"success": true, "value": "test"}'
        processed = await _process_tool_result(json_string, "test_tool")

        assert processed == json_string

    async def test_process_tool_result_task_manager_error(self):
        """Test handling TaskManager processing errors."""
        # Create a mock TaskManager that raises an exception
        mock_task_manager = MagicMock()

        # Create an async mock that raises an exception
        async def mock_process_result(result):
            raise Exception("TaskManager error")

        mock_task_manager.process_result = mock_process_result
        set_task_manager(mock_task_manager)

        result = Result.ok("test data")
        processed = await _process_tool_result(result, "test_tool")

        # Should still return valid JSON despite TaskManager error
        assert isinstance(processed, str)
        assert "test data" in processed
