"""Integration tests for read_resource tool."""

from typing import Any, Callable
from unittest.mock import AsyncMock, patch

import pytest

from mcp_guide.result import Result
from mcp_guide.tools.tool_resource import ReadResourceArgs, internal_read_resource


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory: Callable[[list[str]], Any]) -> Any:
    """Create MCP server with resource tool."""
    return mcp_server_factory(["tool_resource"])


class TestReadResourceContent:
    """Content URI integration tests."""

    @pytest.mark.anyio
    async def test_content_uri(self, mcp_server: Any) -> None:
        """Content URI should delegate to internal_get_content."""
        mock_result = Result.ok("docs content")

        with patch(
            "mcp_guide.tools.tool_resource.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get:
            args = ReadResourceArgs(uri="guide://docs")
            result = await internal_read_resource(args)

            mock_get.assert_called_once()
            content_args = mock_get.call_args[0][0]
            assert content_args.expression == "docs"
            assert content_args.pattern is None

    @pytest.mark.anyio
    async def test_content_uri_with_pattern(self, mcp_server: Any) -> None:
        """Content URI with pattern should pass pattern to get_content."""
        mock_result = Result.ok("readme content")

        with patch(
            "mcp_guide.tools.tool_resource.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get:
            args = ReadResourceArgs(uri="guide://docs/readme")
            result = await internal_read_resource(args)

            content_args = mock_get.call_args[0][0]
            assert content_args.expression == "docs"
            assert content_args.pattern == "readme"


class TestReadResourceCommand:
    """Command URI integration tests."""

    @pytest.mark.anyio
    async def test_command_uri(self, mcp_server: Any) -> None:
        """Command URI should delegate to handle_command."""
        mock_result = Result.ok("project info")
        commands = [{"name": "project"}]

        with patch("mcp_guide.tools.tool_resource.handle_command", new=AsyncMock(return_value=mock_result)) as mock_cmd:
            with patch("mcp_guide.tools.tool_resource.get_session", new=AsyncMock()) as mock_session:
                session = mock_session.return_value
                session.get_docroot = AsyncMock(return_value="/fake")

                with patch("mcp_guide.tools.tool_resource.discover_commands", new=AsyncMock(return_value=commands)):
                    mock_ctx = AsyncMock()
                    args = ReadResourceArgs(uri="guide://_project")
                    result = await internal_read_resource(args, ctx=mock_ctx)

                    mock_cmd.assert_called_once_with("project", kwargs={}, args=[], ctx=mock_ctx)

    @pytest.mark.anyio
    async def test_command_uri_with_args_and_kwargs(self, mcp_server: Any) -> None:
        """Command URI with args and kwargs should pass them to handle_command."""
        mock_result = Result.ok("openspec output")
        commands = [{"name": "openspec/show"}]

        with patch("mcp_guide.tools.tool_resource.handle_command", new=AsyncMock(return_value=mock_result)) as mock_cmd:
            with patch("mcp_guide.tools.tool_resource.get_session", new=AsyncMock()) as mock_session:
                session = mock_session.return_value
                session.get_docroot = AsyncMock(return_value="/fake")

                with patch("mcp_guide.tools.tool_resource.discover_commands", new=AsyncMock(return_value=commands)):
                    mock_ctx = AsyncMock()
                    args = ReadResourceArgs(uri="guide://_openspec/show/my-change?verbose=true")
                    result = await internal_read_resource(args, ctx=mock_ctx)

                    mock_cmd.assert_called_once_with(
                        "openspec/show", kwargs={"verbose": True}, args=["my-change"], ctx=mock_ctx
                    )


class TestReadResourceValidation:
    """Validation and error handling tests."""

    @pytest.mark.anyio
    async def test_invalid_scheme(self, mcp_server: Any) -> None:
        """Non-guide:// URI should return validation error."""
        args = ReadResourceArgs(uri="http://example.com")
        result = await internal_read_resource(args)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert "guide://" in result.error

    @pytest.mark.anyio
    async def test_command_uri_without_context(self, mcp_server: Any) -> None:
        """Command URI without ctx should return clear error."""
        args = ReadResourceArgs(uri="guide://_project")
        result = await internal_read_resource(args, ctx=None)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert "Context" in result.error
