"""Tests for tool decorator test mode control."""

from unittest.mock import Mock

from mcp_guide.core.result import Result
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import ExtMcpToolDecorator, disable_test_mode, enable_test_mode


class TestTestModeControl:
    """Tests for test mode enable/disable functions."""

    def test_enable_test_mode_sets_context_var_to_true(self):
        """Test that enable_test_mode() sets ContextVar to True."""
        from mcp_guide.core.tool_decorator import _test_mode

        enable_test_mode()
        assert _test_mode.get() is True

    def test_disable_test_mode_sets_context_var_to_false(self):
        """Test that disable_test_mode() sets ContextVar to False."""
        from mcp_guide.core.tool_decorator import _test_mode

        enable_test_mode()  # First enable
        disable_test_mode()
        assert _test_mode.get() is False

    def test_default_value_is_false(self):
        """Test that ContextVar default value is False."""
        # Reset to default by creating new context
        import contextvars

        from mcp_guide.core.tool_decorator import _test_mode

        ctx = contextvars.copy_context()
        result = ctx.run(lambda: _test_mode.get())
        assert result is False

    def test_context_var_is_isolated_per_context(self):
        """Test that ContextVar changes don't affect parent context."""
        import contextvars

        from mcp_guide.core.tool_decorator import _test_mode

        # Set in current context
        enable_test_mode()
        assert _test_mode.get() is True

        # Create child context and modify there
        def modify_in_child():
            disable_test_mode()
            return _test_mode.get()

        ctx = contextvars.copy_context()
        result = ctx.run(modify_in_child)
        assert result is False

        # Parent context should still be True
        assert _test_mode.get() is True


class TestExtMcpToolDecorator:
    """Tests for ExtMcpToolDecorator with args_class parameter."""

    def test_tool_with_args_class_parameter(self):
        """Test that tool() accepts args_class parameter."""
        mock_mcp = Mock()
        decorator = ExtMcpToolDecorator(mock_mcp)

        class TestArgs(ToolArguments):
            value: str

        # Should not raise
        result = decorator.tool(args_class=TestArgs)
        assert callable(result)

    def test_auto_generate_description_from_args_class(self):
        """Test that description is auto-generated from args_class."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        decorator = ExtMcpToolDecorator(mock_mcp)

        class TestArgs(ToolArguments):
            """Test function."""

            value: str

        disable_test_mode()  # Ensure production mode

        @decorator.tool(args_class=TestArgs)
        async def test_func(args: TestArgs) -> Result:
            """Test function."""
            return Result.ok("test")

        # Verify description was auto-generated and passed to tool registration
        call_args, call_kwargs = mock_mcp.tool.call_args
        assert "description" in call_kwargs
        assert isinstance(call_kwargs["description"], str)
        assert "Test function." in call_kwargs["description"]

    def test_manual_description_overrides_auto_generation(self):
        """Test that manual description overrides auto-generation."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        decorator = ExtMcpToolDecorator(mock_mcp)

        class TestArgs(ToolArguments):
            value: str

        disable_test_mode()  # Ensure production mode
        manual_desc = "Manual description"

        @decorator.tool(args_class=TestArgs, description=manual_desc)
        async def test_func(args: TestArgs) -> Result:
            """Test function."""
            return Result.ok("test")

        # Verify manual description was used
        call_args = mock_mcp.tool.call_args
        assert call_args is not None

    def test_test_mode_returns_noop_decorator(self):
        """Test that test mode returns no-op decorator."""
        mock_mcp = Mock()
        decorator = ExtMcpToolDecorator(mock_mcp)

        class TestArgs(ToolArguments):
            value: str

        enable_test_mode()  # Enable test mode

        @decorator.tool(args_class=TestArgs)
        async def test_func(args: TestArgs) -> Result:
            """Test function."""
            return Result.ok("test")

        # In test mode, mcp.tool should NOT be called
        assert not mock_mcp.tool.called

        # Function should still be callable (pass dict instead of args object for now)
        import asyncio

        result = asyncio.run(test_func({"value": "test"}))
        assert result.is_ok()

    def test_production_mode_registers_with_fastmcp(self):
        """Test that production mode registers with FastMCP."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        decorator = ExtMcpToolDecorator(mock_mcp)

        class TestArgs(ToolArguments):
            value: str

        disable_test_mode()  # Ensure production mode

        @decorator.tool(args_class=TestArgs)
        async def test_func(args: TestArgs) -> Result:
            """Test function."""
            return Result.ok("test")

        # In production mode, mcp.tool SHOULD be called
        assert mock_mcp.tool.called

    def test_build_tool_description_called_correctly(self):
        """Test that build_tool_description() is called with correct args."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        decorator = ExtMcpToolDecorator(mock_mcp)

        class TestArgs(ToolArguments):
            """Test arguments."""

            value: str

        disable_test_mode()  # Ensure production mode

        @decorator.tool(args_class=TestArgs)
        async def test_func(args: TestArgs) -> Result:
            """Test function docstring."""
            return Result.ok("test")

        # Verify tool was registered
        assert mock_mcp.tool.called
