"""Integration tests for @guide prompt."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_core.result import Result
from mcp_guide.prompts.guide_prompt import guide
from mcp_guide.prompts.guide_prompt_args import GuidePromptArguments


class TestGuidePromptIntegration:
    """Integration tests for @guide prompt functionality."""

    @pytest.mark.asyncio
    async def test_guide_prompt_with_command(self):
        """@guide prompt should call internal_get_content with command parameter."""
        args = GuidePromptArguments(command="test_category")
        mock_ctx = MagicMock()

        # Mock the internal_get_content function to return Result
        mock_result = Result.ok("Test content from category")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            result = await guide(args, mock_ctx)

            # Should call internal_get_content with correct arguments
            mock_get_content.assert_awaited_once()
            args_call, kwargs_call = mock_get_content.call_args
            content_args = args_call[0]  # First positional arg (ContentArgs)
            ctx_arg = args_call[1]  # Second positional arg (ctx)
            assert content_args.category_or_collection == "test_category"
            assert ctx_arg is mock_ctx

            # Should return the content
            assert result == "Test content from category"

    @pytest.mark.asyncio
    async def test_guide_prompt_with_error(self):
        """@guide prompt should handle internal_get_content errors gracefully."""
        args = GuidePromptArguments(command="nonexistent")
        mock_ctx = MagicMock()

        # Mock the internal_get_content function to return error Result
        mock_result = Result.failure("Category not found")

        with patch("mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)):
            result = await guide(args, mock_ctx)

            # Should return error message
            assert result == "Error: Category not found"

    @pytest.mark.asyncio
    async def test_guide_prompt_without_command(self):
        """@guide prompt should provide help when no command given."""
        args = GuidePromptArguments()  # command=None
        mock_ctx = MagicMock()

        result = await guide(args, mock_ctx)

        # Should return help message
        assert "Guide prompt usage" in result
        assert "@guide <category_or_pattern>" in result
        assert "Examples:" in result

    @pytest.mark.asyncio
    async def test_guide_prompt_with_empty_command(self):
        """@guide prompt should provide help when command is empty string."""
        args = GuidePromptArguments(command="")
        mock_ctx = MagicMock()

        result = await guide(args, mock_ctx)

        # Should return help message
        assert "Guide prompt usage" in result

    @pytest.mark.asyncio
    async def test_guide_prompt_with_arguments_reserved(self):
        """@guide prompt should accept arguments but not use them in MVP."""
        args = GuidePromptArguments(command="test", arguments=["arg1", "arg2"])
        mock_ctx = MagicMock()

        # Mock successful internal_get_content
        mock_result = Result.ok("Test content")

        with patch(
            "mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            result = await guide(args, mock_ctx)

            # Should only use command, ignore arguments for MVP
            call_args = mock_get_content.call_args[0][0]
            assert call_args.category_or_collection == "test"
            assert result == "Test content"

    @pytest.mark.asyncio
    async def test_guide_prompt_invalid_json(self):
        """@guide prompt should handle Result objects directly (no JSON parsing needed)."""
        args = GuidePromptArguments(command="test")
        mock_ctx = MagicMock()

        # Mock Result with string content
        mock_result = Result.ok("Direct string response")

        with patch("mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)):
            result = await guide(args, mock_ctx)

            # Should return the string directly from Result
            assert result == "Direct string response"

    @pytest.mark.asyncio
    async def test_guide_prompt_missing_data_field(self):
        """@guide prompt should handle empty content in successful Result."""
        args = GuidePromptArguments(command="test")
        mock_ctx = MagicMock()

        # Mock Result with empty content
        mock_result = Result.ok("")

        with patch("mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)):
            result = await guide(args, mock_ctx)

            # Should return empty string when content is empty
            assert result == ""

    @pytest.mark.asyncio
    async def test_guide_prompt_missing_error_field(self):
        """@guide prompt should handle Result failure with error message."""
        args = GuidePromptArguments(command="test")
        mock_ctx = MagicMock()

        # Mock Result with failure and error message
        mock_result = Result.failure("Something went wrong")

        with patch("mcp_guide.prompts.guide_prompt.internal_get_content", new=AsyncMock(return_value=mock_result)):
            result = await guide(args, mock_ctx)

            # Should return error message
            assert result == "Error: Something went wrong"
