"""Tests for tool_result helper function."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastmcp.tools.base import ToolResult

from mcp_guide.result import Result
from mcp_guide.tools.tool_result import tool_result


class TestToolResult:
    """Tests for tool_result function."""

    @pytest.mark.anyio
    async def test_returns_native_structured_response(self) -> None:
        """Tool results retain Guide data without JSON-string serialization."""
        result = Result.ok(value={"data": "test"})
        output = await tool_result("test_tool", result)

        assert isinstance(output, ToolResult)
        assert output.structured_content["success"] is True
        assert output.structured_content["value"] == {"data": "test"}

    @pytest.mark.anyio
    async def test_logs_result_at_trace_level(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that tool_result logs at TRACE level."""
        import logging

        caplog.set_level(logging.DEBUG)  # TRACE is below DEBUG, but we can check the call

        result = Result.ok(value={"test": "data"})
        await tool_result("my_tool", result)

        # Note: TRACE level logs may not appear in caplog depending on configuration
        # This test verifies the function doesn't raise errors during logging

    @pytest.mark.anyio
    async def test_handles_failure_result(self) -> None:
        """Test that tool_result handles failure results."""
        result = Result.failure(error="Something went wrong", error_type="test_error")
        output = await tool_result("failing_tool", result)

        assert isinstance(output, ToolResult)
        assert output.is_error is True
        assert output.structured_content["success"] is False
        assert output.structured_content["error"] == "Something went wrong"
        assert output.structured_content["error_type"] == "test_error"

    @pytest.mark.anyio
    async def test_handles_result_with_instruction(self) -> None:
        """Test that tool_result preserves instruction field."""
        result = Result.ok(value={"data": "test"}, instruction="Do something")
        output = await tool_result("instructed_tool", result)

        assert isinstance(output, ToolResult)
        assert output.structured_content["instruction"] == "Do something"

    @pytest.mark.anyio
    async def test_handles_result_with_message(self) -> None:
        """Test that tool_result preserves message field."""
        result = Result.ok(value={"data": "test"}, message="Operation completed")
        output = await tool_result("message_tool", result)

        assert isinstance(output, ToolResult)
        assert output.structured_content["message"] == "Operation completed"

    @pytest.mark.anyio
    async def test_does_not_resolve_session_when_session_id_is_missing(self, monkeypatch) -> None:
        """Failed bind paths must not mint a Session from tool_result."""

        async def boom(*_args, **_kwargs):
            raise AssertionError("tool_result must not resolve a Session without session_id")

        monkeypatch.setattr("mcp_guide.session.get_session", boom)
        result = Result.failure("bind failed", error_type="invalid_name")
        output = await tool_result("set_project", result, ctx=object(), session_id=None)

        assert isinstance(output, ToolResult)
        assert output.is_error is True
        assert output.structured_content["error"] == "bind failed"

    @pytest.mark.anyio
    async def test_processes_an_already_resolved_session_without_session_id(self, monkeypatch) -> None:
        """Unbound modern tools still run TaskManager when session_id is unset."""

        async def boom(*_args, **_kwargs):
            raise AssertionError("tool_result must not mint a Session when one is already supplied")

        monkeypatch.setattr("mcp_guide.session.get_session", boom)
        session = MagicMock()
        session.session_id = None
        session.task_manager.process_result = AsyncMock(side_effect=lambda result: result)
        result = Result.ok(value={"data": "test"})

        output = await tool_result("list_tools", result, session=session, session_id=None)

        session.task_manager.process_result.assert_awaited_once_with(result)
        assert isinstance(output, ToolResult)
        assert output.structured_content["success"] is True
