"""Integration tests for Guide resource application handlers."""

import json
from typing import Any, Callable
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp.resources import ResourceResult

from mcp_guide.result import Result
from mcp_guide.runtime import RequestContext
from tests.helpers import create_unbound_test_session, request_context_for


def _parse_result(result: ResourceResult) -> dict[str, Any]:
    """Read Guide's JSON payload from a native resource response."""
    return json.loads(result.contents[0].content)


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory: Callable[[list[str]], Any]) -> Any:
    """Create MCP server with resource handlers."""
    return mcp_server_factory([])


@pytest.fixture
async def request_context(runtime, mcp_server, tmp_path) -> RequestContext:
    """Construct the resolved application input used below the resource boundary."""
    session = create_unbound_test_session(runtime)
    return await request_context_for(session, "resource-session")


async def _guide_resource(
    collection: str,
    document: str,
    request_context: RequestContext,
    *,
    request_uri: str | None = None,
) -> ResourceResult:
    """Invoke the resource application handler after its FastMCP boundary."""
    from mcp_guide.resources import guide_resource

    handler = getattr(guide_resource, "__wrapped__")
    result = await handler(
        collection,
        document,
        request_context=request_context,
        request_uri=request_uri,
    )
    assert isinstance(result, ResourceResult)
    return result


async def _guide_command_resource(
    command_path: str,
    request_context: RequestContext,
    *,
    request_uri: str | None = None,
) -> ResourceResult:
    """Invoke the command resource application handler after its boundary."""
    from mcp_guide.resources import guide_command_resource

    handler = getattr(guide_command_resource, "__wrapped__")
    result = await handler(
        command_path,
        request_context=request_context,
        request_uri=request_uri,
    )
    assert isinstance(result, ResourceResult)
    return result


class TestResourceHandlers:
    """Resource delegation retains the RequestContext resolved at entry."""

    @pytest.mark.anyio
    async def test_guide_resource_passes_the_resolved_context(self, mcp_server, request_context) -> None:
        """Content dispatch receives exactly the context resolved by the boundary."""
        mock_result = Result.ok("Test content from collection")
        with patch("mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=mock_result)) as get_content:
            result = await _guide_resource("docs", "readme", request_context)

        get_content.assert_awaited_once()
        call = get_content.await_args
        assert call is not None
        args, supplied_context = call.args
        assert args.expression == "docs"
        assert args.pattern == "readme"
        assert supplied_context is request_context
        payload = _parse_result(result)
        assert payload["success"] is True
        assert payload["value"] == "Test content from collection"

    @pytest.mark.anyio
    async def test_guide_resource_preserves_empty_document_and_policies_path(self, mcp_server, request_context) -> None:
        """Resource-specific URI rules are applied before content delegation."""
        with patch(
            "mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=Result.ok("content"))
        ) as get_content:
            await _guide_resource("docs", "", request_context)
            call = get_content.await_args
            assert call is not None
            assert call.args[0].pattern is None

            await _guide_resource("policies", "git/ops", request_context)
            call = get_content.await_args
            assert call is not None
            assert call.args[0].pattern == "git/ops/"

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        ("exception", "expected_error"),
        [
            (ValueError("Invalid value"), "Invalid value"),
            (FileNotFoundError("File not found"), "File not found"),
            (PermissionError("Permission denied"), "Permission denied"),
            (Exception("Unexpected error"), "Unexpected error: Unexpected error"),
        ],
    )
    async def test_guide_resource_serialises_content_errors(
        self, mcp_server, request_context, exception: Exception, expected_error: str
    ) -> None:
        """Resource errors remain native resource responses after context propagation."""
        with patch("mcp_guide.resources.internal_get_content", new=AsyncMock(side_effect=exception)):
            payload = _parse_result(await _guide_resource("docs", "readme", request_context))

        assert payload["success"] is False
        assert payload["error"] == expected_error

    @pytest.mark.anyio
    async def test_command_resource_passes_context_and_complete_uri(self, mcp_server, request_context) -> None:
        """Command resources use the same context and preserve URI query arguments."""
        with patch(
            "mcp_guide.resources.internal_read_resource", new=AsyncMock(return_value=Result.ok("status output"))
        ) as read_resource:
            result = await _guide_command_resource(
                "status",
                request_context,
                request_uri="guide://_status?verbose=true",
            )

        read_resource.assert_awaited_once()
        call = read_resource.await_args
        assert call is not None
        args, supplied_context = call.args
        assert args.uri == "guide://_status?verbose=true"
        assert supplied_context is request_context
        assert _parse_result(result)["value"] == "status output"

    @pytest.mark.anyio
    async def test_command_resource_returns_delegated_failure(self, mcp_server, request_context) -> None:
        """Delegated command failures retain their Guide error payload."""
        with patch(
            "mcp_guide.resources.internal_read_resource",
            new=AsyncMock(return_value=Result.failure("Command not found")),
        ):
            payload = _parse_result(await _guide_command_resource("unknown", request_context))

        assert payload["success"] is False
        assert payload["error"] == "Command not found"
