"""Tests for command template functionality."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_guide.prompts.guide_prompt import guide


class TestCommandTemplates:
    """Test command template rendering and functionality."""

    @pytest.mark.asyncio
    async def test_status_command_template(self) -> None:
        """Should render status command template with system information."""
        mock_ctx = MagicMock()
        mock_ctx.session.project_root = "/test/project"

        # Mock template rendering to return formatted status
        with patch("mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock()) as mock_handle:
            from mcp_guide.result import Result

            status_content = """# System Status

**Current Project:** test-project
**Agent:** Claude v3.5
**Command Prefix:** /

## Project Details
**Categories:** docs, examples
**Collections:** getting-started

## Available Commands
- **help**: Shows available commands and usage information
- **status**: Shows system status and current project information"""

            mock_handle.return_value = Result.ok(status_content)

            result_str = await guide(":status", ctx=mock_ctx)

            mock_handle.assert_called_once()
            args = mock_handle.call_args[0]
            command_path, kwargs, args_list = args[:3]

            assert command_path == "status"
            assert kwargs == {}
            assert args_list == []

            result = json.loads(result_str)
            assert result["success"] is True
            assert "System Status" in result["value"]
            assert "Current Project:" in result["value"]
            assert "Available Commands" in result["value"]

    @pytest.mark.asyncio
    async def test_create_collection_command_with_args(self) -> None:
        """Should handle create/collection command with arguments."""
        mock_ctx = MagicMock()
        mock_ctx.session.project_root = "/test/project"

        with patch("mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock()) as mock_handle:
            from mcp_guide.result import Result

            create_content = """# Create Collection: my-docs

Creating collection "my-docs" with categories: docs, examples

Collection created successfully!"""

            mock_handle.return_value = Result.ok(create_content)

            result_str = await guide(":create/collection", "my-docs", "docs", "examples", ctx=mock_ctx)

            mock_handle.assert_called_once()
            args = mock_handle.call_args[0]
            command_path, kwargs, args_list = args[:3]

            assert command_path == "create/collection"
            assert kwargs == {}
            assert args_list == ["my-docs", "docs", "examples"]

            result = json.loads(result_str)
            assert result["success"] is True
            assert "Create Collection: my-docs" in result["value"]
            assert "docs, examples" in result["value"]

    @pytest.mark.asyncio
    async def test_template_rendering_error(self) -> None:
        """Should handle template rendering errors gracefully."""
        mock_ctx = MagicMock()
        mock_ctx.session.project_root = "/test/project"

        with patch("mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock()) as mock_handle:
            from mcp_guide.result import Result

            mock_handle.return_value = Result.failure(
                "Template rendering failed: Invalid syntax", error_type="template_error"
            )

            result_str = await guide(":broken-template", ctx=mock_ctx)

            result = json.loads(result_str)
            assert result["success"] is False
            assert "Template rendering failed" in result["error"]
