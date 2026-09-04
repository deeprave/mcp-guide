"""Tests for Arguments base class."""

from typing import Literal

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

    def test_extra_fields_are_ignored(self):
        """Unknown fields are ignored so leftover caller arguments are not protocol errors."""
        args = SimpleArgs(name="test", unknown_field="value")

        assert args.name == "test"
        assert not hasattr(args, "unknown_field")


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

    def test_to_schema_markdown_optional_union_is_not_any(self):
        """Optional and union fields should not advertise as any."""
        schema = SimpleArgs.to_schema_markdown()

        assert "session_id" in schema
        assert "string | null" in schema
        assert "FastMCP session identifier" not in schema
        assert "Opaque Guide interaction identifier" in schema
        session_line = next(line for line in schema.splitlines() if "**session_id**" in line)
        assert ": any" not in session_line

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
