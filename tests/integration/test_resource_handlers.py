"""Integration tests for MCP resource handlers."""

import json
from types import SimpleNamespace
from typing import Any, Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_guide.result import Result


def _parse_result(result_str: str) -> dict:
    """Parse a JSON result string from a resource handler."""
    return json.loads(result_str)


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory: Callable[[list[str]], Any]) -> Any:
    """Create MCP server with resource handlers."""
    return mcp_server_factory([])


class TestResourceHandlers:
    """Integration tests for MCP resource handlers."""

    @pytest.mark.anyio
    async def test_guide_resource_success(self, mcp_server: Any) -> None:
        """guide:// resource should delegate to internal_get_content."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("Test content from collection")

        with patch(
            "mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            # Access the registered resource handler directly
            from mcp_guide.resources import guide_resource

            result = await guide_resource("docs", "readme", mock_ctx)

            mock_get_content.assert_called_once()
            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.expression == "docs"
            assert content_args.pattern == "readme"
            parsed = _parse_result(result)
            assert parsed["success"] is True
            assert parsed["value"] == "Test content from collection"

    @pytest.mark.anyio
    async def test_guide_resource_no_document(self, mcp_server: Any) -> None:
        """guide:// resource should handle empty document parameter."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("All docs content")

        with patch(
            "mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            # Access the registered resource handler
            from mcp_guide.resources import guide_resource

            result = await guide_resource("docs", "", mock_ctx)

            mock_get_content.assert_called_once()
            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.expression == "docs"
            assert content_args.pattern is None
            parsed = _parse_result(result)
            assert parsed["success"] is True
            assert parsed["value"] == "All docs content"

    @pytest.mark.anyio
    async def test_guide_resource_content_error(self, mcp_server: Any) -> None:
        """guide:// resource should handle internal_get_content errors."""
        mock_ctx = MagicMock()
        mock_result: Result[str] = Result.failure("Collection not found")

        with patch("mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=mock_result)):
            from mcp_guide.resources import guide_resource

            result = await guide_resource("nonexistent", "", mock_ctx)

            parsed = _parse_result(result)
            assert parsed["success"] is False
            assert parsed["error"] == "Collection not found"

    @pytest.mark.anyio
    async def test_guide_resource_exception_handling(self, mcp_server: Any) -> None:
        """guide:// resource should handle unexpected exceptions."""
        mock_ctx = MagicMock()

        with patch(
            "mcp_guide.resources.internal_get_content", new=AsyncMock(side_effect=Exception("Unexpected error"))
        ):
            from mcp_guide.resources import guide_resource

            result = await guide_resource("docs", "readme", mock_ctx)

            assert "Unexpected error: Unexpected error" in result

    @pytest.mark.anyio
    async def test_guide_resource_value_error_handling(self, mcp_server: Any) -> None:
        """guide:// resource should handle ValueError specifically."""
        mock_ctx = MagicMock()

        with patch("mcp_guide.resources.internal_get_content", new=AsyncMock(side_effect=ValueError("Invalid value"))):
            from mcp_guide.resources import guide_resource

            result = await guide_resource("docs", "readme", mock_ctx)

            parsed = _parse_result(result)
            assert parsed["success"] is False
            assert parsed["error"] == "Invalid value"

    @pytest.mark.anyio
    async def test_guide_resource_file_not_found_error_handling(self, mcp_server: Any) -> None:
        """guide:// resource should handle FileNotFoundError specifically."""
        mock_ctx = MagicMock()

        with patch(
            "mcp_guide.resources.internal_get_content", new=AsyncMock(side_effect=FileNotFoundError("File not found"))
        ):
            from mcp_guide.resources import guide_resource

            result = await guide_resource("docs", "readme", mock_ctx)

            parsed = _parse_result(result)
            assert parsed["success"] is False
            assert parsed["error"] == "File not found"

    @pytest.mark.anyio
    async def test_guide_resource_permission_error_handling(self, mcp_server: Any) -> None:
        """guide:// resource should handle PermissionError specifically."""
        mock_ctx = MagicMock()

        with patch(
            "mcp_guide.resources.internal_get_content", new=AsyncMock(side_effect=PermissionError("Permission denied"))
        ):
            from mcp_guide.resources import guide_resource

            result = await guide_resource("docs", "readme", mock_ctx)

            parsed = _parse_result(result)
            assert parsed["success"] is False
            assert parsed["error"] == "Permission denied"

    @pytest.mark.anyio
    async def test_guide_resource_empty_result(self, mcp_server: Any) -> None:
        """guide:// resource should handle empty content results."""
        mock_ctx = MagicMock()
        mock_result = Result.ok(None)

        with patch("mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=mock_result)):
            from mcp_guide.resources import guide_resource

            result = await guide_resource("docs", "readme", mock_ctx)

            parsed = _parse_result(result)
            assert parsed["success"] is True
            assert parsed.get("value") is None

    @pytest.mark.anyio
    async def test_guide_command_resource_routes_simple_command_uri(self, mcp_server: Any) -> None:
        """Command resource should delegate to internal_read_resource."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("project info")

        with patch(
            "mcp_guide.resources.internal_read_resource", new=AsyncMock(return_value=mock_result)
        ) as mock_read_resource:
            from mcp_guide.resources import guide_command_resource

            result = await guide_command_resource("project", mock_ctx)

            mock_read_resource.assert_called_once()
            args_call, kwargs_call = mock_read_resource.call_args
            read_args = args_call[0]
            assert read_args.uri == "guide://_project"
            assert kwargs_call["ctx"] is mock_ctx
            parsed = _parse_result(result)
            assert parsed["success"] is True
            assert parsed["value"] == "project info"

    @pytest.mark.anyio
    async def test_guide_command_resource_uses_full_request_uri(self, mcp_server: Any) -> None:
        """Command resource should preserve query params from the MCP request URI.

        Uses AnyUrl (as the MCP protocol provides) rather than str, to match the real
        type of ReadResourceRequestParams.uri and catch isinstance(uri, str) regressions.
        """
        from pydantic import AnyUrl

        request = SimpleNamespace(params=SimpleNamespace(uri=AnyUrl("guide://_status?verbose=true")))
        mock_ctx = MagicMock()
        mock_ctx.request_context = SimpleNamespace(request=request)
        mock_result = Result.ok("status output")

        with patch(
            "mcp_guide.resources.internal_read_resource", new=AsyncMock(return_value=mock_result)
        ) as mock_read_resource:
            from mcp_guide.resources import guide_command_resource

            result = await guide_command_resource("status", mock_ctx)

            read_args = mock_read_resource.call_args[0][0]
            assert read_args.uri == "guide://_status?verbose=true"
            parsed = _parse_result(result)
            assert parsed["success"] is True
            assert parsed["value"] == "status output"

    @pytest.mark.anyio
    async def test_guide_command_resource_supports_path_args(self, mcp_server: Any) -> None:
        """Command resource should preserve command path arguments."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("category output")

        with patch(
            "mcp_guide.resources.internal_read_resource", new=AsyncMock(return_value=mock_result)
        ) as mock_read_resource:
            from mcp_guide.resources import guide_command_resource

            result = await guide_command_resource("category/add/docs", mock_ctx)

            read_args = mock_read_resource.call_args[0][0]
            assert read_args.uri == "guide://_category/add/docs"
            parsed = _parse_result(result)
            assert parsed["success"] is True
            assert parsed["value"] == "category output"

    @pytest.mark.anyio
    async def test_guide_command_resource_returns_validation_errors(self, mcp_server: Any) -> None:
        """Command resource should surface validation failures as text."""
        mock_ctx = MagicMock()
        mock_result = Result.failure("Command not found")

        with patch("mcp_guide.resources.internal_read_resource", new=AsyncMock(return_value=mock_result)):
            from mcp_guide.resources import guide_command_resource

            result = await guide_command_resource("unknown", mock_ctx)

            parsed = _parse_result(result)
            assert parsed["success"] is False
            assert parsed["error"] == "Command not found"

    @pytest.mark.anyio
    async def test_policies_topic_uri_appends_trailing_slash(self, mcp_server: Any) -> None:
        """guide://policies/<topic> passes pattern with trailing slash for sub-path filtering."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("policy content")

        with patch(
            "mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            from mcp_guide.resources import guide_resource

            result = await guide_resource("policies", "git/ops", mock_ctx)

            mock_get_content.assert_called_once()
            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.expression == "policies"
            assert content_args.pattern == "git/ops/"
            parsed = _parse_result(result)
            assert parsed["success"] is True

    @pytest.mark.anyio
    async def test_policies_without_topic_does_not_append_slash(self, mcp_server: Any) -> None:
        """guide://policies with no topic passes pattern=None as normal."""
        mock_ctx = MagicMock()
        mock_result = Result.ok("all policies")

        with patch(
            "mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=mock_result)
        ) as mock_get_content:
            from mcp_guide.resources import guide_resource

            result = await guide_resource("policies", "", mock_ctx)

            mock_get_content.assert_called_once()
            args_call, _ = mock_get_content.call_args
            content_args = args_call[0]
            assert content_args.expression == "policies"
            assert content_args.pattern is None
