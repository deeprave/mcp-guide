"""Tests for prompt decorator infrastructure."""

import os
from unittest.mock import MagicMock, patch

from mcp_core.arguments import Arguments
from mcp_core.prompt_decorator import ExtMcpPromptDecorator


class SamplePromptArgs(Arguments):
    """Test prompt arguments."""

    command: str
    count: int = 5


class TestExtMcpPromptDecorator:
    """Tests for ExtMcpPromptDecorator."""

    def test_init_reads_mcp_prompt_prefix_env_var(self):
        """Decorator should read MCP_PROMPT_PREFIX environment variable."""
        mock_mcp = MagicMock()

        with patch.dict(os.environ, {"MCP_PROMPT_PREFIX": "test"}):
            decorator = ExtMcpPromptDecorator(mock_mcp)
            assert decorator.prefix == "test"

    def test_init_defaults_to_empty_prefix(self):
        """Decorator should default to empty prefix when env var not set."""
        mock_mcp = MagicMock()

        with patch.dict(os.environ, {}, clear=True):
            decorator = ExtMcpPromptDecorator(mock_mcp)
            assert decorator.prefix == ""

    def test_prompt_decorator_with_prefix(self):
        """Prompt decorator should add prefix to prompt name."""
        mock_mcp = MagicMock()

        with patch.dict(os.environ, {"MCP_PROMPT_PREFIX": "custom"}):
            decorator = ExtMcpPromptDecorator(mock_mcp)

            @decorator.prompt(args_class=SamplePromptArgs)
            def test_prompt(args: SamplePromptArgs) -> str:
                """Test prompt function."""
                return "test"

            # Should register with prefixed name
            mock_mcp.prompt.assert_called_once()
            call_kwargs = mock_mcp.prompt.call_args[1]
            assert call_kwargs["name"] == "custom_test_prompt"

    def test_prompt_decorator_without_prefix(self):
        """Prompt decorator should use original name when no prefix."""
        mock_mcp = MagicMock()

        with patch.dict(os.environ, {}, clear=True):
            decorator = ExtMcpPromptDecorator(mock_mcp)

            @decorator.prompt(args_class=SamplePromptArgs)
            def test_prompt(args: SamplePromptArgs) -> str:
                """Test prompt function."""
                return "test"

            # Should register with original name
            mock_mcp.prompt.assert_called_once()
            call_kwargs = mock_mcp.prompt.call_args[1]
            assert call_kwargs["name"] == "test_prompt"

    def test_prompt_decorator_generates_description_from_args_class(self):
        """Prompt decorator should generate description from Arguments class."""
        mock_mcp = MagicMock()
        decorator = ExtMcpPromptDecorator(mock_mcp)

        @decorator.prompt(args_class=SamplePromptArgs)
        def test_prompt(args: SamplePromptArgs) -> str:
            """Test prompt docstring."""
            return "test"

        # Should call build_description and use result
        mock_mcp.prompt.assert_called_once()
        call_kwargs = mock_mcp.prompt.call_args[1]
        description = call_kwargs["description"]

        assert "Test prompt docstring." in description
        assert "## Arguments" in description
        assert "command" in description
