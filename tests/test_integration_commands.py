"""Integration tests for command-based prompt system."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_guide.prompts.guide_prompt import guide


class TestCommandIntegration:
    """Test complete command system integration."""

    @pytest.fixture
    def mock_ctx(self):
        """Create mock context with temporary project root."""
        ctx = MagicMock()
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx.session.project_root = temp_dir
            ctx.session.get_docroot = AsyncMock(return_value=temp_dir)
            yield ctx

    @pytest.fixture
    def commands_setup(self, mock_ctx):
        """Set up commands directory with test templates."""
        project_root = Path(mock_ctx.session.project_root)
        commands_dir = project_root / "_commands"
        commands_dir.mkdir()

        # Create test command template
        test_template = commands_dir / "test.mustache"
        test_template.write_text("""---
type: guide-command
description: Test command
required_args: []
optional_args: []
required_kwargs: []
optional_kwargs: [verbose]
---
Test command executed successfully!
{{#kwargs.verbose}}Verbose mode enabled.{{/kwargs.verbose}}
{{#args}}{{.}} {{/args}}
""")

        return commands_dir

    @pytest.mark.asyncio
    async def test_command_vs_content_routing(self, mock_ctx, commands_setup):
        """Test that commands and content are routed correctly."""
        with (
            patch("mcp_guide.prompts.guide_prompt.get_template_contexts", new=AsyncMock()) as mock_context,
            patch(
                "mcp_guide.session.get_or_create_session", new=AsyncMock(return_value=mock_ctx.session)
            ) as mock_session,
        ):
            from mcp_guide.utils.template_context import TemplateContext

            mock_context.return_value = TemplateContext({})

            # Test command routing (should use command handler)
            result_str = await guide(":test", ctx=mock_ctx)
            result = json.loads(result_str)
            assert result["success"] is True
            assert "Test command executed successfully!" in result["value"]

            # Test content routing (should use get_content)
            with patch("mcp_guide.prompts.guide_prompt.internal_get_content") as mock_get_content:
                from mcp_guide.result import Result

                mock_get_content.return_value = Result.ok("Regular content")

                result_str = await guide("docs", ctx=mock_ctx)
                result = json.loads(result_str)
                assert result["success"] is True
                mock_get_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_argument_parsing_integration(self, mock_ctx, commands_setup):
        """Test argument parsing with real command execution."""
        with (
            patch("mcp_guide.prompts.guide_prompt.get_template_contexts", new=AsyncMock()) as mock_context,
            patch(
                "mcp_guide.session.get_or_create_session", new=AsyncMock(return_value=mock_ctx.session)
            ) as mock_session,
        ):
            from mcp_guide.utils.template_context import TemplateContext

            mock_context.return_value = TemplateContext({})

            # Test with flags and arguments
            result_str = await guide(":test", "--verbose", "arg1", "arg2", ctx=mock_ctx)
            result = json.loads(result_str)

            assert result["success"] is True
            assert "Test command executed successfully!" in result["value"]
            assert "Verbose mode enabled." in result["value"]
            assert "arg1 arg2" in result["value"]

    @pytest.mark.asyncio
    async def test_security_validation_integration(self, mock_ctx):
        """Test security validation in real command flow."""
        # Test directory traversal prevention
        result_str = await guide(":../../../etc/passwd", ctx=mock_ctx)
        result = json.loads(result_str)
        assert result["success"] is False
        assert "security validation failed" in result["error"].lower()

        # Test command injection prevention
        result_str = await guide(":test;rm", ctx=mock_ctx)
        result = json.loads(result_str)
        assert result["success"] is False
        assert "security validation failed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_help_system_integration(self, mock_ctx, commands_setup):
        """Test help system with real command discovery."""
        with (
            patch("mcp_guide.prompts.guide_prompt.get_template_contexts", new=AsyncMock()) as mock_context,
            patch(
                "mcp_guide.session.get_or_create_session", new=AsyncMock(return_value=mock_ctx.session)
            ) as mock_session,
        ):
            from mcp_guide.utils.template_context import TemplateContext

            mock_context.return_value = TemplateContext({})

            # Create help template
            help_template = commands_setup / "help.mustache"
            help_template.write_text("""---
type: guide-command
description: Show help information
required_args: []
optional_args: [command]
required_kwargs: []
optional_kwargs: []
---
Available commands:
{{#commands}}
- {{name}}: {{description}}
{{/commands}}
""")

            result_str = await guide(":help", ctx=mock_ctx)
            result = json.loads(result_str)

            assert result["success"] is True
            assert "Available commands:" in result["value"]
            assert "test: Test command" in result["value"]
            assert "help: Show help information" in result["value"]

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, mock_ctx):
        """Test error handling in complete flow."""
        # Test missing commands directory
        result_str = await guide(":nonexistent", ctx=mock_ctx)
        result = json.loads(result_str)
        assert result["success"] is False
        assert "commands directory not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_multiple_expressions_regression(self, mock_ctx):
        """Test that multiple expressions still work for content."""
        with patch("mcp_guide.prompts.guide_prompt.internal_get_content") as mock_get_content:
            from mcp_guide.result import Result

            mock_get_content.return_value = Result.ok("Combined content")

            result_str = await guide("docs", "examples", "tests", ctx=mock_ctx)
            result = json.loads(result_str)

            assert result["success"] is True
            # Should call internal_get_content with comma-separated expressions
            mock_get_content.assert_called_once()
            call_args = mock_get_content.call_args[0]
            assert "docs,examples,tests" in str(call_args)

    @pytest.mark.asyncio
    async def test_subcommand_integration(self, mock_ctx, commands_setup):
        """Test subcommand routing and execution."""
        # Create subcommand directory and template
        info_dir = commands_setup / "info"
        info_dir.mkdir()

        project_template = info_dir / "project.mustache"
        project_template.write_text("""---
type: guide-command
description: Show project information
required_args: []
optional_args: []
required_kwargs: []
optional_kwargs: []
---
Project Information:
Current project: {{project.name}}
""")

        with (
            patch("mcp_guide.prompts.guide_prompt.get_template_contexts", new=AsyncMock()) as mock_context,
            patch(
                "mcp_guide.session.get_or_create_session", new=AsyncMock(return_value=mock_ctx.session)
            ) as mock_session,
        ):
            from mcp_guide.utils.template_context import TemplateContext

            mock_context.return_value = TemplateContext({"project": {"name": "test-project"}})

            result_str = await guide(":info/project", ctx=mock_ctx)
            result = json.loads(result_str)

            assert result["success"] is True
            assert "Project Information:" in result["value"]
            assert "Current project: test-project" in result["value"]

    @pytest.mark.asyncio
    async def test_semicolon_prefix_integration(self, mock_ctx, commands_setup):
        """Test semicolon prefix works the same as colon."""
        with (
            patch("mcp_guide.prompts.guide_prompt.get_template_contexts", new=AsyncMock()) as mock_context,
            patch(
                "mcp_guide.session.get_or_create_session", new=AsyncMock(return_value=mock_ctx.session)
            ) as mock_session,
        ):
            from mcp_guide.utils.template_context import TemplateContext

            mock_context.return_value = TemplateContext({})

            # Test semicolon prefix
            result_str = await guide(";test", "--verbose", ctx=mock_ctx)
            result = json.loads(result_str)

            assert result["success"] is True
            assert "Test command executed successfully!" in result["value"]
            assert "Verbose mode enabled." in result["value"]

    @pytest.mark.asyncio
    async def test_front_matter_validation_integration(self, mock_ctx, commands_setup):
        """Test front matter validation with real templates."""
        # Create command with required arguments
        strict_template = commands_setup / "strict.mustache"
        strict_template.write_text("""---
type: guide-command
description: Strict command with required args
required_args: [name]
optional_args: []
required_kwargs: [type]
optional_kwargs: []
---
Hello {{args.0}}, type: {{kwargs.type}}
""")

        with (
            patch("mcp_guide.prompts.guide_prompt.get_template_contexts", new=AsyncMock()) as mock_context,
            patch(
                "mcp_guide.session.get_or_create_session", new=AsyncMock(return_value=mock_ctx.session)
            ) as mock_session,
        ):
            from mcp_guide.utils.template_context import TemplateContext

            mock_context.return_value = TemplateContext({})

            # Test missing required arguments - should fail validation
            result_str = await guide(":strict", ctx=mock_ctx)
            result = json.loads(result_str)
            assert result["success"] is False
            assert "missing required" in result["error"].lower()

            # Test with required arguments - should succeed
            result_str = await guide(":strict", "--type=user", "John", ctx=mock_ctx)
            result = json.loads(result_str)
            assert result["success"] is True
            assert "Hello John, type: user" in result["value"]
