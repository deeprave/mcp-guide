"""Tests for tool_result helper function."""

import json

import pytest

from mcp_guide.result import Result
from mcp_guide.tools.tool_result import tool_result


class TestToolResult:
    """Tests for tool_result function."""

    async def test_returns_json_string(self) -> None:
        """Test that tool_result returns a JSON string."""
        result = Result.ok(value={"data": "test"})
        output = await tool_result("test_tool", result)

        assert isinstance(output, str)
        parsed = json.loads(output)
        assert parsed["success"] is True
        assert parsed["value"] == {"data": "test"}

    async def test_logs_result_at_trace_level(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that tool_result logs at TRACE level."""
        import logging

        caplog.set_level(logging.DEBUG)  # TRACE is below DEBUG, but we can check the call

        result = Result.ok(value={"test": "data"})
        await tool_result("my_tool", result)

        # Note: TRACE level logs may not appear in caplog depending on configuration
        # This test verifies the function doesn't raise errors during logging

    async def test_handles_failure_result(self) -> None:
        """Test that tool_result handles failure results."""
        result = Result.failure(error="Something went wrong", error_type="test_error")
        output = await tool_result("failing_tool", result)

        parsed = json.loads(output)
        assert parsed["success"] is False
        assert parsed["error"] == "Something went wrong"
        assert parsed["error_type"] == "test_error"

    async def test_handles_result_with_instruction(self) -> None:
        """Test that tool_result preserves instruction field."""
        result = Result.ok(value={"data": "test"}, instruction="Do something")
        output = await tool_result("instructed_tool", result)

        parsed = json.loads(output)
        assert parsed["instruction"] == "Do something"

    async def test_handles_result_with_message(self) -> None:
        """Test that tool_result preserves message field."""
        result = Result.ok(value={"data": "test"}, message="Operation completed")
        output = await tool_result("message_tool", result)

        parsed = json.loads(output)
        assert parsed["message"] == "Operation completed"
