"""Integration tests for MCP resource handlers."""

from typing import Any, Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_core.result import Result


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory: Callable[[list[str]], Any]) -> Any:
    """Create MCP server with resource handlers."""
    return mcp_server_factory([])


class TestResourceHandlers:
    """Integration tests for MCP resource handlers."""

    @pytest.mark.asyncio
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
            assert content_args.category_or_collection == "docs"
            assert content_args.pattern == "readme"
            assert result == "Test content from collection"

    @pytest.mark.asyncio
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
            assert content_args.category_or_collection == "docs"
            assert content_args.pattern is None
            assert result == "All docs content"

    @pytest.mark.asyncio
    async def test_guide_resource_content_error(self, mcp_server: Any) -> None:
        """guide:// resource should handle internal_get_content errors."""
        mock_ctx = MagicMock()
        mock_result: Result[str] = Result.failure("Collection not found")

        with patch("mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=mock_result)):
            from mcp_guide.resources import guide_resource

            result = await guide_resource("nonexistent", "", mock_ctx)

            assert result == "Collection not found"

    @pytest.mark.asyncio
    async def test_guide_resource_exception_handling(self, mcp_server: Any) -> None:
        """guide:// resource should handle unexpected exceptions."""
        mock_ctx = MagicMock()

        with patch(
            "mcp_guide.resources.internal_get_content", new=AsyncMock(side_effect=Exception("Unexpected error"))
        ):
            from mcp_guide.resources import guide_resource

            result = await guide_resource("docs", "readme", mock_ctx)

            assert "Unexpected error: Unexpected error" in result

    @pytest.mark.asyncio
    async def test_guide_resource_empty_result(self, mcp_server: Any) -> None:
        """guide:// resource should handle empty content results."""
        mock_ctx = MagicMock()
        mock_result = Result.ok(None)

        with patch("mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=mock_result)):
            from mcp_guide.resources import guide_resource

            result = await guide_resource("docs", "readme", mock_ctx)

            assert result == ""

    @pytest.mark.asyncio
    async def test_mcp_client_can_list_resources(self, tmp_path: Any) -> None:
        """Test that MCP client can list guide:// resources."""
        import asyncio
        import sys

        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        # Server parameters - run mcp-guide server
        server_params = StdioServerParameters(
            command=sys.executable, args=["-m", "mcp_guide.main"], env={"MCP_GUIDE_CONFIG_DIR": str(tmp_path)}
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize with timeout
                await asyncio.wait_for(session.initialize(), timeout=5.0)

                # List resource templates - verify guide:// URIs are registered
                templates_result = await asyncio.wait_for(session.list_resource_templates(), timeout=5.0)
                template_uris = [template.uriTemplate for template in templates_result.resourceTemplates]

                # Should contain guide:// URI template
                guide_templates = [uri for uri in template_uris if uri.startswith("guide://")]
                assert len(guide_templates) > 0, f"No guide:// templates found. Available: {template_uris}"

                # Should specifically have our template
                expected_template = "guide://{collection}/{document}"
                assert expected_template in template_uris, f"Expected {expected_template} not found in {template_uris}"
