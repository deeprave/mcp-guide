"""Integration tests for guide prompt functionality."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_guide.result import Result
from mcp_guide.result_constants import INSTRUCTION_DISPLAY_ONLY, INSTRUCTION_ERROR_MESSAGE


class TestGuidePromptIntegration:
    """Integration tests for @guide prompt."""

    @pytest.mark.asyncio
    async def test_guide_prompt_with_command(self, guide_function) -> None:
        """@guide prompt should call internal_get_content with command parameter."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Test content from category")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            result_str = await guide_function("test_category", ctx=mock_ctx)

            mock_get_content.assert_called_once()
            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.expression == "test_category"
            assert content_args.pattern is None

            result = json.loads(result_str)
            assert result["success"] is True
            assert result["value"] == "Test content from category"
            assert result["instruction"] == INSTRUCTION_DISPLAY_ONLY

    @pytest.mark.asyncio
    async def test_guide_prompt_with_error(self, guide_function) -> None:
        """@guide prompt should handle internal_get_content errors gracefully."""
        mock_ctx = MagicMock()
        mock_result: Result[str] = Result.failure("Category not found")

        with patch("mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)):
            result_str = await guide_function("nonexistent", ctx=mock_ctx)

            result = json.loads(result_str)
            assert result["success"] is False
            assert result["error"] == "Category not found"
            assert result["instruction"] == INSTRUCTION_ERROR_MESSAGE

    @pytest.mark.asyncio
    async def test_guide_prompt_without_command(self, guide_function) -> None:
        """@guide prompt should return usage error when no arguments given."""
        mock_ctx = MagicMock()

        result_str = await guide_function(ctx=mock_ctx)

        result = json.loads(result_str)
        assert result["success"] is False
        assert "guide prompt requires one or more arguments" in result["error"]
        assert ":help" in result["error"]
        assert result["error_type"] == "validation"
        assert result["instruction"] == INSTRUCTION_ERROR_MESSAGE

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scenario,args,kwargs,expected_expression",
        [
            ("none_termination", ("a",), {"arg3": "c"}, "a"),  # arg2 is None, stops at "a"
            ("argument_ordering", ("first",), {"arg2": "second"}, "first,second"),
            ("multiple_arguments", ("lang/python", "advanced", "tutorial"), {}, "lang/python,advanced,tutorial"),
            (
                "maximum_arguments",
                ("1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F"),
                {},
                "1,2,3,4,5,6,7,8,9,A,B,C,D,E,F",
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_argv_parsing(self, guide_function, scenario, args, kwargs, expected_expression) -> None:
        """Test argv parsing with different argument scenarios."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Test content")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            await guide_function(*args, **kwargs, ctx=mock_ctx)

            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.expression == expected_expression

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scenario,command,expected_error",
        [
            ("empty_string", "", "guide prompt requires one or more arguments"),
            ("colon_only", ":", "Command name cannot be empty"),
            ("semicolon_only", ";", "Command name cannot be empty"),
        ],
        ids=["empty_string", "colon_only", "semicolon_only"],
    )
    @pytest.mark.asyncio
    async def test_guide_prompt_empty_command_scenarios(
        self, guide_function, scenario, command, expected_error
    ) -> None:
        """@guide prompt should handle various empty command scenarios."""
        mock_ctx = MagicMock()

        result_str = await guide_function(command, ctx=mock_ctx)
        result = json.loads(result_str)
        assert result["success"] is False
        assert expected_error in result["error"]
        if scenario == "empty_string":
            assert ":help" in result["error"]
            assert result["instruction"] == INSTRUCTION_ERROR_MESSAGE

    @pytest.mark.asyncio
    async def test_guide_prompt_with_arguments_reserved(self, guide_function) -> None:
        """@guide prompt should use all arguments for content access."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Test content")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            result_str = await guide_function("test", "arg1", "arg2", ctx=mock_ctx)

            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.expression == "test,arg1,arg2"

            result = json.loads(result_str)
            assert result["success"] is True
            assert result["value"] == "Test content"
            assert result["instruction"] == INSTRUCTION_DISPLAY_ONLY

    @pytest.mark.asyncio
    async def test_guide_prompt_with_content_result(self, guide_function) -> None:
        """@guide prompt should handle Result objects directly."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Plain text content, not JSON")

        with patch("mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)):
            result_str = await guide_function("test", ctx=mock_ctx)

            result = json.loads(result_str)
            assert result["success"] is True
            assert result["value"] == "Plain text content, not JSON"
            assert result["instruction"] == INSTRUCTION_DISPLAY_ONLY

    @pytest.mark.asyncio
    async def test_guide_prompt_with_empty_content(self, guide_function) -> None:
        """@guide prompt should handle empty content in successful Result."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("")

        with patch("mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)):
            result_str = await guide_function("test", ctx=mock_ctx)

            result = json.loads(result_str)
            assert result["success"] is True
            assert result["value"] == ""
            assert result["instruction"] == INSTRUCTION_DISPLAY_ONLY

    @pytest.mark.asyncio
    async def test_guide_prompt_with_multiple_expressions(self, guide_function) -> None:
        """@guide prompt should join multiple expressions with commas."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Combined content")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            result_str = await guide_function("review,review/pr+commit", "lang/python", ctx=mock_ctx)

            mock_get_content.assert_called_once()
            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            # Should join all arguments with commas
            assert content_args.expression == "review,review/pr+commit,lang/python"
            assert content_args.pattern is None

            result = json.loads(result_str)
            assert result["success"] is True
            assert result["value"] == "Combined content"
            assert result["instruction"] == INSTRUCTION_DISPLAY_ONLY

    @pytest.mark.asyncio
    async def test_guide_prompt_with_colon_command(self, guide_function) -> None:
        """@guide prompt should route :command to separate command handler."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Help content")

        with patch(
            "mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock(return_value=mock_result)
        ) as mock_handle_command:
            result_str = await guide_function(":help", ctx=mock_ctx)

            mock_handle_command.assert_called_once()
            call_kwargs = mock_handle_command.call_args
            assert call_kwargs[0][0] == "help"  # command_path is first positional
            assert call_kwargs[1]["argv"] == [":help"]

            result = json.loads(result_str)
            assert result["success"] is True
            assert result["value"] == "Help content"

    @pytest.mark.asyncio
    async def test_guide_prompt_with_semicolon_command(self, guide_function) -> None:
        """@guide prompt should route ;command to separate command handler."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Status content")

        with patch(
            "mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock(return_value=mock_result)
        ) as mock_handle_command:
            await guide_function(";status", ctx=mock_ctx)

            mock_handle_command.assert_called_once()
            call_kwargs = mock_handle_command.call_args
            assert call_kwargs[0][0] == "status"
            assert call_kwargs[1]["argv"] == [";status"]

    @pytest.mark.asyncio
    async def test_guide_prompt_with_subcommand(self, guide_function) -> None:
        """@guide prompt should handle subcommands like :create/category."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Create category content")

        with patch(
            "mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock(return_value=mock_result)
        ) as mock_handle_command:
            await guide_function(":create/category", ctx=mock_ctx)

            mock_handle_command.assert_called_once()
            call_kwargs = mock_handle_command.call_args
            assert call_kwargs[0][0] == "create/category"
            assert call_kwargs[1]["argv"] == [":create/category"]

    @pytest.mark.asyncio
    async def test_guide_prompt_with_command_arguments(self, guide_function) -> None:
        """@guide prompt should pass raw argv to handle_command for deferred parsing."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Command with args")

        with patch(
            "mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock(return_value=mock_result)
        ) as mock_handle_command:
            await guide_function(":create/collection", "--verbose", "description=test", "arg1", "arg2", ctx=mock_ctx)

            # Verify command handler was called with raw argv
            mock_handle_command.assert_called_once()
            call_kwargs = mock_handle_command.call_args
            assert call_kwargs[0][0] == "create/collection"
            assert call_kwargs[1]["argv"] == [
                ":create/collection",
                "--verbose",
                "description=test",
                "arg1",
                "arg2",
            ]

    @pytest.mark.asyncio
    async def test_guide_prompt_with_parse_errors(self, guide_function) -> None:
        """@guide prompt should return failure for argument parsing errors via _execute_command."""
        mock_ctx = MagicMock()

        # Mock _execute_command to simulate parse error from deferred parsing
        error_result = Result.failure(
            "Argument parsing failed: Invalid flag: --bad=; Missing key: =value", error_type="validation"
        )
        with patch("mcp_guide.prompts.guide_prompt._execute_command", new=AsyncMock(return_value=error_result)):
            result_str = await guide_function(":create", "--bad=", "=value", ctx=mock_ctx)

            result = json.loads(result_str)
            assert result["success"] is False
            assert "Argument parsing failed" in result["error"]
            assert "--bad=" in result["error"]
            assert "=value" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_command_returns_failure_on_template_errors(self, guide_function) -> None:
        """_execute_command should return Result.failure when rendered.errors is non-empty."""
        from pathlib import Path
        from unittest.mock import AsyncMock, patch

        from mcp_guide.render.content import RenderedContent
        from mcp_guide.render.frontmatter import Frontmatter

        mock_ctx = MagicMock()
        rendered = RenderedContent(
            frontmatter=Frontmatter({}),
            frontmatter_length=0,
            content="",
            content_length=0,
            template_path=Path("fake/command.mustache"),
            template_name="command.mustache",
            errors=["Missing required argument: name"],
        )

        with patch("mcp_guide.prompts.guide_prompt.render_template", new=AsyncMock(return_value=rendered)):
            result_str = await guide_function(":project/category/add", ctx=mock_ctx)

        result = json.loads(result_str)
        assert result["success"] is False
        assert result["error_type"] == "validation"
        assert result["error_data"]["errors"] == ["Missing required argument: name"]
