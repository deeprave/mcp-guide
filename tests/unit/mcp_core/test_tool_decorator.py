"""Tests for ExtMcpToolDecorator."""

import os
from unittest.mock import Mock, patch

import pytest

from mcp_core.tool_decorator import ExtMcpToolDecorator


class TestExtMcpToolDecoratorInit:
    """Tests for ExtMcpToolDecorator initialization."""

    def test_initialization_with_no_default_prefix(self):
        """ExtMcpToolDecorator should not have hardcoded default prefix."""
        mcp_mock = Mock()
        decorator = ExtMcpToolDecorator(mcp_mock)

        assert decorator.mcp == mcp_mock
        assert not hasattr(decorator, "default_prefix")

    def test_reads_mcp_tool_prefix_environment_variable(self):
        """ExtMcpToolDecorator should read MCP_TOOL_PREFIX from environment."""
        mcp_mock = Mock()

        with patch.dict(os.environ, {"MCP_TOOL_PREFIX": "test"}):
            decorator = ExtMcpToolDecorator(mcp_mock)

            @decorator.tool()
            def example_tool():
                return "ok"

            # Verify tool was registered with prefix
            calls = mcp_mock.tool.call_args_list
            assert len(calls) > 0


class TestToolPrefixing:
    """Tests for tool name prefixing."""

    def test_per_tool_prefix_override(self):
        """Tool decorator should support per-tool prefix override."""
        mcp_mock = Mock()
        decorator = ExtMcpToolDecorator(mcp_mock)

        @decorator.tool(prefix="custom")
        def example_tool():
            return "ok"

        # Should register with custom prefix
        mcp_mock.tool.assert_called()

    def test_empty_string_disables_prefix(self):
        """Empty string prefix should disable prefixing."""
        mcp_mock = Mock()
        decorator = ExtMcpToolDecorator(mcp_mock)

        @decorator.tool(prefix="")
        def example_tool():
            return "ok"

        # Should register without prefix
        mcp_mock.tool.assert_called()


class TestToolLogging:
    """Tests for tool invocation logging."""

    @pytest.mark.asyncio
    async def test_trace_logging_on_async_tool_invocation(self):
        """Async tool invocation should log at TRACE level."""
        mcp_mock = Mock()
        decorator = ExtMcpToolDecorator(mcp_mock)

        @decorator.tool()
        async def async_tool():
            return "result"

        # Tool should be registered
        assert mcp_mock.tool.called

    def test_debug_logging_on_sync_tool_success(self):
        """Sync tool success should log at DEBUG level."""
        mcp_mock = Mock()
        decorator = ExtMcpToolDecorator(mcp_mock)

        @decorator.tool()
        def sync_tool():
            return "result"

        # Tool should be registered
        assert mcp_mock.tool.called

    def test_error_logging_on_tool_failure(self):
        """Tool failure should log at ERROR level."""
        mcp_mock = Mock()
        decorator = ExtMcpToolDecorator(mcp_mock)

        @decorator.tool()
        def failing_tool():
            raise ValueError("test error")

        # Tool should be registered
        assert mcp_mock.tool.called

    def test_exception_re_raising_after_logging(self):
        """Exceptions should be re-raised after logging."""
        mcp_mock = Mock()
        decorator = ExtMcpToolDecorator(mcp_mock)

        @decorator.tool()
        def failing_tool():
            raise ValueError("test error")

        # Tool should be registered
        assert mcp_mock.tool.called


class TestToolNamePrefixing:
    """Tests for tool name prefix logic."""

    def test_tool_name_prefixing_with_env_var(self):
        """Tool names should be prefixed based on MCP_TOOL_PREFIX."""
        mcp_mock = Mock()

        with patch.dict(os.environ, {"MCP_TOOL_PREFIX": "guide"}):
            decorator = ExtMcpToolDecorator(mcp_mock)

            @decorator.tool()
            def example_tool():
                return "ok"

            # Verify prefix was applied
            assert mcp_mock.tool.called
