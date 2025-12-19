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
            # Access the registered resource handler
            from mcp_guide.resources import register_resource_handlers

            # Create a temporary server to get the handler
            temp_handlers: dict[str, Callable[..., Any]] = {}

            class MockServer:
                def resource(self, uri_template: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
                    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                        temp_handlers[uri_template] = func
                        return func

                    return decorator

            mock_server = MockServer()
            register_resource_handlers(mock_server)

            # Get the handler and test it
            handler = temp_handlers["guide://{collection}/{document}"]
            result = await handler("docs", "readme", mock_ctx)

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
            from mcp_guide.resources import register_resource_handlers

            temp_handlers: dict[str, Callable[..., Any]] = {}

            class MockServer:
                def resource(self, uri_template: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
                    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                        temp_handlers[uri_template] = func
                        return func

                    return decorator

            mock_server = MockServer()
            register_resource_handlers(mock_server)

            handler = temp_handlers["guide://{collection}/{document}"]
            result = await handler("docs", "", mock_ctx)

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
            from mcp_guide.resources import register_resource_handlers

            temp_handlers: dict[str, Callable[..., Any]] = {}

            class MockServer:
                def resource(self, uri_template: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
                    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                        temp_handlers[uri_template] = func
                        return func

                    return decorator

            mock_server = MockServer()
            register_resource_handlers(mock_server)

            handler = temp_handlers["guide://{collection}/{document}"]
            result = await handler("nonexistent", "", mock_ctx)

            assert result == "Collection not found"

    @pytest.mark.asyncio
    async def test_guide_resource_exception_handling(self, mcp_server: Any) -> None:
        """guide:// resource should handle unexpected exceptions."""
        mock_ctx = MagicMock()

        with patch(
            "mcp_guide.resources.internal_get_content", new=AsyncMock(side_effect=Exception("Unexpected error"))
        ):
            from mcp_guide.resources import register_resource_handlers

            temp_handlers: dict[str, Callable[..., Any]] = {}

            class MockServer:
                def resource(self, uri_template: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
                    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                        temp_handlers[uri_template] = func
                        return func

                    return decorator

            mock_server = MockServer()
            register_resource_handlers(mock_server)

            handler = temp_handlers["guide://{collection}/{document}"]
            result = await handler("docs", "readme", mock_ctx)

            assert "Unexpected error: Unexpected error" in result

    @pytest.mark.asyncio
    async def test_guide_resource_empty_result(self, mcp_server: Any) -> None:
        """guide:// resource should handle empty content results."""
        mock_ctx = MagicMock()
        mock_result = Result.ok(None)

        with patch("mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=mock_result)):
            from mcp_guide.resources import register_resource_handlers

            temp_handlers: dict[str, Callable[..., Any]] = {}

            class MockServer:
                def resource(self, uri_template: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
                    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                        temp_handlers[uri_template] = func
                        return func

                    return decorator

            mock_server = MockServer()
            register_resource_handlers(mock_server)

            handler = temp_handlers["guide://{collection}/{document}"]
            result = await handler("docs", "readme", mock_ctx)

            assert result == ""
