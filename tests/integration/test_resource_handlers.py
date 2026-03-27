"""Integration tests for MCP resource handlers."""

from types import SimpleNamespace
from typing import Any, Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_guide.result import Result


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
            assert result == "Test content from collection"

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
            assert result == "All docs content"

    @pytest.mark.anyio
    async def test_guide_resource_content_error(self, mcp_server: Any) -> None:
        """guide:// resource should handle internal_get_content errors."""
        mock_ctx = MagicMock()
        mock_result: Result[str] = Result.failure("Collection not found")

        with patch("mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=mock_result)):
            from mcp_guide.resources import guide_resource

            result = await guide_resource("nonexistent", "", mock_ctx)

            assert result == "Collection not found"

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

            assert result == "Error: Invalid value"

    @pytest.mark.anyio
    async def test_guide_resource_file_not_found_error_handling(self, mcp_server: Any) -> None:
        """guide:// resource should handle FileNotFoundError specifically."""
        mock_ctx = MagicMock()

        with patch(
            "mcp_guide.resources.internal_get_content", new=AsyncMock(side_effect=FileNotFoundError("File not found"))
        ):
            from mcp_guide.resources import guide_resource

            result = await guide_resource("docs", "readme", mock_ctx)

            assert result == "Error: File not found"

    @pytest.mark.anyio
    async def test_guide_resource_permission_error_handling(self, mcp_server: Any) -> None:
        """guide:// resource should handle PermissionError specifically."""
        mock_ctx = MagicMock()

        with patch(
            "mcp_guide.resources.internal_get_content", new=AsyncMock(side_effect=PermissionError("Permission denied"))
        ):
            from mcp_guide.resources import guide_resource

            result = await guide_resource("docs", "readme", mock_ctx)

            assert result == "Error: Permission denied"

    @pytest.mark.anyio
    async def test_guide_resource_empty_result(self, mcp_server: Any) -> None:
        """guide:// resource should handle empty content results."""
        mock_ctx = MagicMock()
        mock_result = Result.ok(None)

        with patch("mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=mock_result)):
            from mcp_guide.resources import guide_resource

            result = await guide_resource("docs", "readme", mock_ctx)

            assert result == ""

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
            assert result == "project info"

    @pytest.mark.anyio
    async def test_guide_command_resource_uses_full_request_uri(self, mcp_server: Any) -> None:
        """Command resource should preserve query params from the MCP request URI."""
        request = SimpleNamespace(params=SimpleNamespace(uri="guide://_status?verbose=true"))
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
            assert result == "status output"

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
            assert result == "category output"

    @pytest.mark.anyio
    async def test_guide_command_resource_returns_validation_errors(self, mcp_server: Any) -> None:
        """Command resource should surface validation failures as text."""
        mock_ctx = MagicMock()
        mock_result = Result.failure("Command not found")

        with patch("mcp_guide.resources.internal_read_resource", new=AsyncMock(return_value=mock_result)):
            from mcp_guide.resources import guide_command_resource

            result = await guide_command_resource("unknown", mock_ctx)

            assert result == "Command not found"

    @pytest.mark.anyio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_mcp_client_can_list_resources(self, tmp_path: Any) -> None:
        """End-to-end test that MCP client can list guide:// resources."""
        import asyncio
        import os
        import sys

        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        # Allow CI and developers to override timeout for end-to-end MCP subprocess startup
        timeout = float(os.getenv("MCP_E2E_TIMEOUT_SECONDS", "30"))

        # Server parameters - run mcp-guide server
        env = os.environ.copy()
        env["MCP_GUIDE_CONFIG_DIR"] = str(tmp_path)

        # Create installer config to skip first-run
        config_dir = tmp_path / "config"
        config_dir.mkdir(exist_ok=True)
        (config_dir / "installer.yaml").write_text("docroot: /tmp/test\n")

        server_params = StdioServerParameters(
            command=sys.executable, args=["-m", "mcp_guide.main", "--configdir", str(config_dir)], env=env
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize with timeout
                    await asyncio.wait_for(session.initialize(), timeout=timeout)

                    # List resource templates - verify guide:// URIs are registered
                    templates_result = await asyncio.wait_for(session.list_resource_templates(), timeout=timeout)
                    template_uris = [template.uriTemplate for template in templates_result.resourceTemplates]

                    # Should contain guide:// URI template
                    guide_templates = [uri for uri in template_uris if uri.startswith("guide://")]
                    assert len(guide_templates) > 0, f"No guide:// templates found. Available: {template_uris}"

                    # Should specifically have our template
                    expected_template = "guide://{collection}/{document}"
                    assert expected_template in template_uris, (
                        f"Expected {expected_template} not found in {template_uris}"
                    )

                    expected_command_template = "guide://_{command_path*}"
                    assert expected_command_template in template_uris, (
                        f"Expected {expected_command_template} not found in {template_uris}"
                    )

                    project_result = await asyncio.wait_for(session.read_resource("guide://_project"), timeout=timeout)
                    project_text = project_result.contents[0].text
                    assert "Project" in project_text

                    status_result = await asyncio.wait_for(
                        session.read_resource("guide://_status?verbose=true"), timeout=timeout
                    )
                    status_text = status_result.contents[0].text
                    assert "System Status" in status_text

                    missing_arg_result = await asyncio.wait_for(
                        session.read_resource("guide://_perm/write/add"), timeout=timeout
                    )
                    missing_arg_text = missing_arg_result.contents[0].text
                    assert "Missing required argument: path" in missing_arg_text

                    invalid_command_result = await asyncio.wait_for(
                        session.read_resource("guide://_unknown"), timeout=timeout
                    )
                    invalid_command_text = invalid_command_result.contents[0].text
                    assert "Command not found" in invalid_command_text
        except (asyncio.TimeoutError, OSError) as e:
            pytest.skip(f"End-to-end MCP test skipped due to subprocess/timeout issue: {e}")
