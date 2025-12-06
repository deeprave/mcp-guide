"""Tests for example tool."""

import pytest

from mcp_core.result import Result
from mcp_guide.tools.tool_example import ExampleArgs, example_tool


class TestExampleTool:
    """Tests for example tool patterns."""

    @pytest.mark.asyncio
    async def test_example_tool_with_all_patterns(self) -> None:
        """Example tool should demonstrate all conventions."""
        args = ExampleArgs(action="demo", message="test")
        result_dict = await example_tool(args)

        assert result_dict["success"] is True
        assert result_dict["value"]["action"] == "demo"
        assert result_dict["value"]["message"] == "test"
        assert "conventions_demonstrated" in result_dict["value"]

    def test_explicit_use_pattern_with_literal_type(self) -> None:
        """Example tool should use Literal type for action."""
        # Valid actions
        args1 = ExampleArgs(action="demo")
        assert args1.action == "demo"

        args2 = ExampleArgs(action="test")
        assert args2.action == "test"

        args3 = ExampleArgs(action="validate")
        assert args3.action == "validate"

        # Invalid action should raise validation error
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ExampleArgs(action="invalid")  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_result_pattern_usage(self) -> None:
        """Example tool should return Result pattern."""
        args = ExampleArgs(action="demo")
        result_dict = await example_tool(args)

        # Should have Result structure
        assert "success" in result_dict
        assert "value" in result_dict
        assert result_dict["success"] is True

    @pytest.mark.asyncio
    async def test_instruction_field_patterns(self) -> None:
        """Example tool should include instruction field."""
        args = ExampleArgs(action="demo")
        result_dict = await example_tool(args)

        assert "instruction" in result_dict
        assert "instruction field" in result_dict["instruction"]
        assert len(result_dict["instruction"]) > 0
