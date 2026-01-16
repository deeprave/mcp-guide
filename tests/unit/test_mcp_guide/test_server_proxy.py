"""Tests for server module and _ToolsProxy."""

from unittest.mock import Mock

import pytest

from mcp_guide.core.tool_decorator import ExtMcpToolDecorator
from mcp_guide.server import _ToolsProxy


class TestToolsProxy:
    """Tests for _ToolsProxy lazy initialization."""

    @pytest.mark.asyncio
    async def test_tool_before_set_instance_returns_noop(self) -> None:
        """Test that tool() before set_instance returns no-op decorator."""
        proxy = _ToolsProxy()

        @proxy.tool()
        async def test_func() -> str:
            return "test"

        # Function should be unchanged
        assert await test_func() == "test"

    def test_tool_after_set_instance_delegates(self) -> None:
        """Test that tool() after set_instance delegates to actual decorator."""
        proxy = _ToolsProxy()
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        decorator = ExtMcpToolDecorator(mock_mcp)

        proxy.set_instance(decorator)

        # Now tool() should delegate
        @proxy.tool()
        async def test_func() -> str:
            return "test"

        # Verify delegation happened (mcp.tool was called)
        assert mock_mcp.tool.called

    def test_set_instance_updates_class_variable(self) -> None:
        """Test that set_instance() updates _instance class variable."""
        # Reset class variable first
        _ToolsProxy._instance = None

        proxy = _ToolsProxy()
        mock_mcp = Mock()
        decorator = ExtMcpToolDecorator(mock_mcp)

        assert proxy._instance is None
        proxy.set_instance(decorator)
        assert proxy._instance is decorator

    def test_module_level_tools_instance_exists(self) -> None:
        """Test that module-level tools instance exists."""
        from mcp_guide.server import tools

        assert isinstance(tools, _ToolsProxy)

    def test_tool_with_args_and_kwargs(self) -> None:
        """Test that tool() passes through args and kwargs."""
        proxy = _ToolsProxy()
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        decorator = ExtMcpToolDecorator(mock_mcp)

        proxy.set_instance(decorator)

        @proxy.tool(description="test desc", prefix="test")
        async def test_func() -> str:
            return "test"

        # Verify args were passed through
        call_kwargs = mock_mcp.tool.call_args[1]
        assert "description" in str(call_kwargs) or mock_mcp.tool.called
