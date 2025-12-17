"""Integration tests for @guide prompt."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_guide.prompts.guide_prompt import guide
from mcp_guide.prompts.guide_prompt_args import GuidePromptArguments


class TestGuidePromptIntegration:
    """Integration tests for @guide prompt functionality."""

    @pytest.mark.asyncio
    async def test_guide_prompt_with_command(self):
        """@guide prompt should call get_content with command parameter."""
        args = GuidePromptArguments(command="test_category")
        mock_ctx = MagicMock()

        # Mock the get_content function to return JSON string
        mock_result_json = '{"success": true, "data": "Test content from category"}'

        with patch("mcp_guide.prompts.guide_prompt.get_content", return_value=mock_result_json) as mock_get_content:
            result = await guide(args, mock_ctx)

            # Should call _get_content with correct arguments
            mock_get_content.assert_called_once()
            call_args = mock_get_content.call_args[0][0]  # First positional arg (ContentArgs)
            assert call_args.category_or_collection == "test_category"

            # Should return the content
            assert result == "Test content from category"

    @pytest.mark.asyncio
    async def test_guide_prompt_with_error(self):
        """@guide prompt should handle get_content errors gracefully."""
        args = GuidePromptArguments(command="nonexistent")
        mock_ctx = MagicMock()

        # Mock the get_content function to return error JSON
        mock_result_json = '{"success": false, "error": "Category not found"}'

        with patch("mcp_guide.prompts.guide_prompt.get_content", return_value=mock_result_json):
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

        # Mock successful get_content
        mock_result_json = '{"success": true, "data": "Test content"}'

        with patch("mcp_guide.prompts.guide_prompt.get_content", return_value=mock_result_json) as mock_get_content:
            result = await guide(args, mock_ctx)

            # Should only use command, ignore arguments for MVP
            call_args = mock_get_content.call_args[0][0]
            assert call_args.category_or_collection == "test"
            assert result == "Test content"
