"""Integration tests for guide prompt functionality."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_core.result import Result
from mcp_guide.prompts.guide_prompt import guide
from mcp_guide.tools.tool_constants import INSTRUCTION_DISPLAY_ONLY


class TestGuidePromptIntegration:
    """Integration tests for @guide prompt."""

    @pytest.mark.asyncio
    async def test_guide_prompt_with_command(self) -> None:
        """@guide prompt should call internal_get_content with command parameter."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Test content from category")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            result_str = await guide("test_category", ctx=mock_ctx)

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
    async def test_guide_prompt_with_error(self) -> None:
        """@guide prompt should handle internal_get_content errors gracefully."""
        mock_ctx = MagicMock()
        mock_result: Result[str] = Result.failure("Category not found")

        with patch("mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)):
            result_str = await guide("nonexistent", ctx=mock_ctx)

            result = json.loads(result_str)
            assert result["success"] is False
            assert result["error"] == "Category not found"
            assert result["instruction"] == INSTRUCTION_DISPLAY_ONLY

    @pytest.mark.asyncio
    async def test_guide_prompt_without_command(self) -> None:
        """@guide prompt should return usage error when no arguments given."""
        mock_ctx = MagicMock()

        result_str = await guide(ctx=mock_ctx)

        result = json.loads(result_str)
        assert result["success"] is False
        assert result["error"] == "Requires 1 or more arguments"
        assert result["error_type"] == "validation"
        assert result["instruction"] == INSTRUCTION_DISPLAY_ONLY

    @pytest.mark.asyncio
    async def test_argv_parsing_none_termination(self) -> None:
        """Argv parsing should stop at first None value."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Test content")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            await guide("a", arg3="c", ctx=mock_ctx)  # arg2 is None, so should stop at "a"

            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.expression == "a"

    @pytest.mark.asyncio
    async def test_argv_parsing_argument_ordering(self) -> None:
        """Argv parsing should maintain correct argument order."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Test content")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            await guide("first", arg2="second", ctx=mock_ctx)  # Both args should be processed

            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.expression == "first,second"

    @pytest.mark.asyncio
    async def test_argv_parsing_multiple_arguments(self) -> None:
        """Argv parsing should handle multiple arguments correctly."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Test content")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            await guide("lang/python", "advanced", "tutorial", ctx=mock_ctx)

            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.expression == "lang/python,advanced,tutorial"

    @pytest.mark.asyncio
    async def test_argv_parsing_maximum_arguments(self) -> None:
        """Argv parsing should handle all 15 arguments."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Test content")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            await guide("1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F", ctx=mock_ctx)

            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.expression == "1,2,3,4,5,6,7,8,9,A,B,C,D,E,F"

    @pytest.mark.asyncio
    async def test_guide_prompt_with_empty_command(self) -> None:
        """@guide prompt should return usage error when command is empty string."""
        mock_ctx = MagicMock()

        result_str = await guide("", ctx=mock_ctx)

        result = json.loads(result_str)
        assert result["success"] is False
        assert result["error"] == "Requires 1 or more arguments"
        assert result["instruction"] == INSTRUCTION_DISPLAY_ONLY

    @pytest.mark.asyncio
    async def test_guide_prompt_with_arguments_reserved(self) -> None:
        """@guide prompt should use all arguments for content access."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Test content")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            result_str = await guide("test", "arg1", "arg2", ctx=mock_ctx)

            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.expression == "test,arg1,arg2"

            result = json.loads(result_str)
            assert result["success"] is True
            assert result["value"] == "Test content"
            assert result["instruction"] == INSTRUCTION_DISPLAY_ONLY

    @pytest.mark.asyncio
    async def test_guide_prompt_with_content_result(self) -> None:
        """@guide prompt should handle Result objects directly."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Plain text content, not JSON")

        with patch("mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)):
            result_str = await guide("test", ctx=mock_ctx)

            result = json.loads(result_str)
            assert result["success"] is True
            assert result["value"] == "Plain text content, not JSON"
            assert result["instruction"] == INSTRUCTION_DISPLAY_ONLY

    @pytest.mark.asyncio
    async def test_guide_prompt_with_empty_content(self) -> None:
        """@guide prompt should handle empty content in successful Result."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("")

        with patch("mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)):
            result_str = await guide("test", ctx=mock_ctx)

            result = json.loads(result_str)
            assert result["success"] is True
            assert result["value"] == ""
            assert result["instruction"] == INSTRUCTION_DISPLAY_ONLY

    @pytest.mark.asyncio
    async def test_guide_prompt_with_multiple_expressions(self) -> None:
        """@guide prompt should join multiple expressions with commas."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Combined content")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            result_str = await guide("review,review/pr+commit", "lang/python", ctx=mock_ctx)

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
    async def test_guide_prompt_with_colon_command(self) -> None:
        """@guide prompt should route :command to separate command handler."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Help content")

        with patch(
            "mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock(return_value=mock_result)
        ) as mock_handle_command:
            result_str = await guide(":help", ctx=mock_ctx)

            mock_handle_command.assert_called_once()
            args = mock_handle_command.call_args[0]
            command_path, kwargs, args_list = args[:3]

            assert command_path == "help"
            assert kwargs == {}
            assert args_list == []

            result = json.loads(result_str)
            assert result["success"] is True
            assert result["value"] == "Help content"

    @pytest.mark.asyncio
    async def test_guide_prompt_with_semicolon_command(self) -> None:
        """@guide prompt should route ;command to separate command handler."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Status content")

        with patch(
            "mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock(return_value=mock_result)
        ) as mock_handle_command:
            await guide(";status", ctx=mock_ctx)

            mock_handle_command.assert_called_once()
            args = mock_handle_command.call_args[0]
            command_path, kwargs, args_list = args[:3]

            assert command_path == "status"
            assert kwargs == {}
            assert args_list == []

    @pytest.mark.asyncio
    async def test_guide_prompt_with_subcommand(self) -> None:
        """@guide prompt should handle subcommands like :create/category."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Create category content")

        with patch(
            "mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock(return_value=mock_result)
        ) as mock_handle_command:
            await guide(":create/category", ctx=mock_ctx)

            mock_handle_command.assert_called_once()
            args = mock_handle_command.call_args[0]
            command_path, kwargs, args_list = args[:3]

            assert command_path == "create/category"
            assert kwargs == {}
            assert args_list == []

    @pytest.mark.asyncio
    async def test_guide_prompt_with_empty_command(self) -> None:
        """@guide prompt should reject empty commands like : or ;."""
        mock_ctx = MagicMock()

        result_str = await guide(":", ctx=mock_ctx)
        result = json.loads(result_str)
        assert result["success"] is False
        assert result["error"] == "Command name cannot be empty"

        result_str = await guide(";", ctx=mock_ctx)
        result = json.loads(result_str)
        assert result["success"] is False
        assert result["error"] == "Command name cannot be empty"

    @pytest.mark.asyncio
    async def test_guide_prompt_with_command_arguments(self) -> None:
        """@guide prompt should parse command arguments."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Command with args")

        with (
            patch(
                "mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock(return_value=mock_result)
            ) as mock_handle_command,
            patch("mcp_guide.prompts.guide_prompt.parse_command_arguments") as mock_parse,
        ):
            # Mock the parser to return expected values
            mock_parse.return_value = (
                {"_verbose": True, "description": "test"},  # kwargs
                ["arg1", "arg2"],  # args
                [],  # parse_errors
            )

            result_str = await guide(
                ":create/collection", "--verbose", "description=test", "arg1", "arg2", ctx=mock_ctx
            )

            # Verify parser was called with correct arguments
            mock_parse.assert_called_once_with([":create/collection", "--verbose", "description=test", "arg1", "arg2"])

            # Verify command handler was called with parsed arguments
            mock_handle_command.assert_called_once()
            args = mock_handle_command.call_args[0]
            command_path, kwargs, args_list = args[:3]

            assert command_path == "create/collection"
            assert kwargs == {"_verbose": True, "description": "test"}
            assert args_list == ["arg1", "arg2"]

    @pytest.mark.asyncio
    async def test_guide_prompt_with_parse_errors(self) -> None:
        """@guide prompt should return failure for argument parsing errors."""
        mock_ctx = MagicMock()

        with patch("mcp_guide.prompts.guide_prompt.parse_command_arguments") as mock_parse:
            # Mock the parser to return parse errors
            mock_parse.return_value = (
                {},  # kwargs
                [],  # args
                ["Invalid flag: --bad=", "Missing key: =value"],  # parse_errors
            )

            result_str = await guide(":create", "--bad=", "=value", ctx=mock_ctx)

            result = json.loads(result_str)
            assert result["success"] is False
            assert "Argument parsing failed" in result["error"]
            assert "--bad=" in result["error"]
            assert "=value" in result["error"]
