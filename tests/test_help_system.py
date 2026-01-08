"""Tests for help system functionality."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestHelpSystem:
    """Test help system integration."""

    @pytest.mark.asyncio
    async def test_help_command_basic(self, guide_function) -> None:
        """Should execute help command and show available commands."""
        mock_ctx = MagicMock()
        mock_ctx.session.project_root = "/test/project"

        # Mock the command handler to return help content
        with patch("mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock()) as mock_handle:
            from mcp_guide.result import Result

            mock_handle.return_value = Result.ok("# Available Commands\n\n## help\nShows available commands")

            result_str = await guide_function(":help", ctx=mock_ctx)

            mock_handle.assert_called_once()
            args = mock_handle.call_args[0]
            command_path, kwargs, args_list = args[:3]

            assert command_path == "help"
            assert kwargs == {}
            assert args_list == []

            result = json.loads(result_str)
            assert result["success"] is True
            assert "Available Commands" in result["value"]
