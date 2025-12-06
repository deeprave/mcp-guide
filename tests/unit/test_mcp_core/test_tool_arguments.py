"""Tests for ToolArguments base class."""

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
