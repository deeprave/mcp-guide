"""Tests for ToolArguments base class."""

import asyncio
from typing import Literal

import pytest
from pydantic import ValidationError

from mcp_core.tool_arguments import ToolArguments


class SimpleArgs(ToolArguments):
    """Simple test arguments."""

    name: str
    count: int = 5


class LiteralArgs(ToolArguments):
    """Arguments with Literal type."""

    action: Literal["create", "update", "delete"]
    target: str


class TestToolArgumentsValidation:
    """Tests for Pydantic validation."""

    def test_base_model_inheritance_and_validation(self):
        """ToolArguments should inherit from BaseModel and validate fields."""
        args = SimpleArgs(name="test", count=10)
        assert args.name == "test"
        assert args.count == 10

    def test_extra_forbid_rejects_unknown_fields(self):
        """ToolArguments should reject unknown fields with extra='forbid'."""
        with pytest.raises(ValidationError) as exc_info:
            SimpleArgs(name="test", unknown_field="value")

        assert "extra_forbidden" in str(exc_info.value)


class TestSchemaGeneration:
    """Tests for schema markdown generation."""

    def test_to_schema_markdown_output_format(self):
        """to_schema_markdown() should generate markdown-formatted schema."""
        schema = SimpleArgs.to_schema_markdown()

        assert "## Arguments" in schema
        assert "name" in schema
        assert "string" in schema.lower()
        assert "count" in schema
        assert "integer" in schema.lower()

    def test_to_schema_markdown_with_literal_types(self):
        """to_schema_markdown() should handle Literal types."""
        schema = LiteralArgs.to_schema_markdown()

        assert "action" in schema
        assert "create" in schema
        assert "update" in schema
        assert "delete" in schema

    def test_build_tool_description_combines_docstring_and_schema(self):
        """build_tool_description() should combine function docstring with schema."""

        def example_tool(args: SimpleArgs) -> dict:
            """This is a test tool."""
            return {}

        description = ToolArguments.build_tool_description(example_tool)

        assert "This is a test tool." in description
        assert "## Arguments" in description


class TestToolCollection:
    """Tests for @ToolArguments.declare decorator."""

    def setup_method(self):
        """Clear declared tools before each test."""
        ToolArguments._declared.clear()

    def test_declare_decorator_collects_tool(self):
        """@ToolArguments.declare should collect tool without wrapping."""

        @ToolArguments.declare
        def test_tool(args: SimpleArgs) -> dict:
            return {"result": "ok"}

        # Function should not be wrapped
        result = test_tool(SimpleArgs(name="test"))
        assert result == {"result": "ok"}

        # Should be in collection
        declared = ToolArguments._declared
        assert "test_tool" in declared

    def test_get_declared_tools_returns_and_clears(self):
        """get_declared_tools() should return collection and clear it."""

        @ToolArguments.declare
        def tool1(args: SimpleArgs) -> dict:
            return {}

        @ToolArguments.declare
        def tool2(args: SimpleArgs) -> dict:
            return {}

        # First call returns tools
        tools = ToolArguments.get_declared_tools()
        assert "tool1" in tools
        assert "tool2" in tools

        # Second call returns empty (cleared)
        tools2 = ToolArguments.get_declared_tools()
        assert len(tools2) == 0

    def test_double_registration_prevention(self):
        """get_declared_tools() clearing prevents double registration."""

        @ToolArguments.declare
        def test_tool(args: SimpleArgs) -> dict:
            return {}

        # First retrieval
        tools1 = ToolArguments.get_declared_tools()
        assert "test_tool" in tools1

        # Second retrieval should be empty
        tools2 = ToolArguments.get_declared_tools()
        assert "test_tool" not in tools2

    @pytest.mark.asyncio
    async def test_asyncio_lock_thread_safety(self):
        """_lock should protect _declared dictionary access."""

        @ToolArguments.declare
        def test_tool(args: SimpleArgs) -> dict:
            return {}

        # Simulate concurrent access
        def get_tools():
            return ToolArguments.get_declared_tools()

        # Run in executor to simulate concurrent access
        loop = asyncio.get_event_loop()
        results = await asyncio.gather(
            loop.run_in_executor(None, get_tools),
            loop.run_in_executor(None, get_tools),
            loop.run_in_executor(None, get_tools),
        )

        # Only one should get the tools, others should get empty
        non_empty = [r for r in results if len(r) > 0]
        assert len(non_empty) == 1
