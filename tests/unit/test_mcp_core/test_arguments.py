"""Tests for Arguments base class."""

from typing import Literal

import pytest
from pydantic import ValidationError

from mcp_guide.core.arguments import Arguments


class SimpleArgs(Arguments):
    """Simple test arguments."""

    name: str
    count: int = 5


class LiteralArgs(Arguments):
    """Arguments with Literal type."""

    action: Literal["create", "update", "delete"]
    target: str


class TestArgumentsValidation:
    """Tests for Pydantic validation."""

    def test_base_model_inheritance_and_validation(self):
        """Arguments should inherit from BaseModel and validate fields."""
        args = SimpleArgs(name="test", count=10)
        assert args.name == "test"
        assert args.count == 10

    def test_extra_forbid_rejects_unknown_fields(self):
        """Arguments should reject unknown fields with extra='forbid'."""
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

    def test_build_description_combines_docstring_and_schema(self):
        """build_description() should combine function docstring with schema."""

        def example_function(args: SimpleArgs) -> dict:
            """This is a test function."""
            return {}

        description = Arguments.build_description(example_function)

        assert "This is a test function." in description
        assert "## Arguments" in description


class TestAliases:
    """Tests for package aliases."""

    def test_toolarguments_alias(self):
        """ToolArguments alias should work for existing code."""
        from mcp_guide.core.tool_arguments import ToolArguments

        assert ToolArguments is Arguments

        class TestArgs(ToolArguments):
            value: str = "test"

        args = TestArgs()
        assert args.value == "test"

    def test_promptarguments_alias(self):
        """PromptArguments alias should work for prompt code."""
        from mcp_guide.prompts import PromptArguments

        assert PromptArguments is Arguments

        class TestPromptArgs(PromptArguments):
            command: str = "test"

        args = TestPromptArgs()
        assert args.command == "test"
