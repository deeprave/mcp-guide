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
            assert content_args.category_or_collection == "test_category"
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
            assert content_args.category_or_collection == "a"

    @pytest.mark.asyncio
    async def test_argv_parsing_argument_ordering(self) -> None:
        """Argv parsing should maintain correct argument order."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Test content")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            await guide("first", arg2="second", ctx=mock_ctx)  # arg1 should be processed, not arg2

            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.category_or_collection == "first"

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
            assert content_args.category_or_collection == "lang/python"

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
            assert content_args.category_or_collection == "1"

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
        """@guide prompt should use first argument for content access."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Test content")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            result_str = await guide("test", "arg1", "arg2", ctx=mock_ctx)

            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.category_or_collection == "test"

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
