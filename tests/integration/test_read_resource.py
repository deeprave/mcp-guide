"""Integration tests for the read_resource application handler."""

from typing import Any, Callable
from unittest.mock import AsyncMock, patch

import pytest

from mcp_guide.result import Result
from mcp_guide.runtime import RequestContext
from mcp_guide.tools.tool_resource import ReadResourceArgs, internal_read_resource
from tests.helpers import create_unbound_test_session, request_context_for


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory: Callable[[list[str]], Any]) -> Any:
    """Create MCP server with resource tool."""
    return mcp_server_factory(["tool_resource"])


@pytest.fixture
async def request_context(runtime, mcp_server, tmp_path) -> RequestContext:
    """Provide the already-resolved context expected by internal routing."""
    return await request_context_for(create_unbound_test_session(runtime), "resource-session")


class TestReadResourceContent:
    """Content URI integration tests."""

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        ("uri", "expression", "pattern"), [("guide://docs", "docs", None), ("guide://docs/readme", "docs", "readme")]
    )
    async def test_content_uri(
        self, mcp_server, request_context, uri: str, expression: str, pattern: str | None
    ) -> None:
        """Content URI dispatch retains the supplied RequestContext."""
        expected = Result.ok("docs content")
        with patch(
            "mcp_guide.tools.tool_resource.internal_get_content", new=AsyncMock(return_value=expected)
        ) as get_content:
            result = await internal_read_resource(ReadResourceArgs(uri=uri), request_context)

        get_content.assert_awaited_once()
        call = get_content.await_args
        assert call is not None
        content_args, supplied_context = call.args
        assert content_args.expression == expression
        assert content_args.pattern == pattern
        assert supplied_context is request_context
        assert result is expected


class TestReadResourceCommand:
    """Command URI integration tests."""

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        ("uri", "commands", "command", "kwargs", "arguments"),
        [
            ("guide://_project", [{"name": "project"}], "project", {}, []),
            (
                "guide://_openspec/show/my-change?verbose=true",
                [{"name": "openspec/show"}],
                "openspec/show",
                {"verbose": True},
                ["my-change"],
            ),
            (
                "guide://_project?table=true",
                [{"name": "project/project", "aliases": ["project?verbose"]}],
                "project",
                {"table": True},
                [],
            ),
        ],
    )
    async def test_command_uri(
        self,
        mcp_server,
        request_context,
        uri: str,
        commands: list[dict[str, Any]],
        command: str,
        kwargs: dict[str, Any],
        arguments: list[str],
    ) -> None:
        """Command routing receives the original RequestContext exactly once."""
        expected = Result.ok("command output")
        with (
            patch(
                "mcp_guide.prompts.guide_prompt.handle_command", new=AsyncMock(return_value=expected)
            ) as handle_command,
            patch("mcp_guide.tools.tool_resource.discover_commands", new=AsyncMock(return_value=commands)),
        ):
            result = await internal_read_resource(ReadResourceArgs(uri=uri), request_context)

        handle_command.assert_awaited_once_with(
            command,
            kwargs=kwargs,
            args=arguments,
            request_context=request_context,
        )
        assert result is expected


class TestReadResourceValidation:
    """Validation and error handling tests."""

    @pytest.mark.anyio
    async def test_invalid_scheme(self, mcp_server, request_context) -> None:
        """Non-guide URI returns a validation result without a new lookup."""
        result = await internal_read_resource(ReadResourceArgs(uri="http://example.com"), request_context)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert result.error is not None
        assert "guide://" in result.error


@pytest.mark.anyio
async def test_read_resource_uri_session_id_resumes_bound_session(runtime, tmp_path) -> None:
    """A unique URI session_id selects the already-bound Session before scope."""
    from types import SimpleNamespace

    from mcp_guide.runtime import OwnerKey
    from mcp_guide.session import bind_session_project, request_context_scope

    session = runtime.resolve_session(OwnerKey("bound-session"))
    session.session_id = "bound-session"
    await bind_session_project(session, "/client/workspace/bound-session")
    runtime.retain_session(OwnerKey("bound-session"), session)

    args = ReadResourceArgs(uri="guide://docs?session_id=bound-session")
    assert args.session_id == "bound-session"

    ctx = SimpleNamespace(
        request_context=SimpleNamespace(
            protocol_version="2026-07-28",
            request_id="uri-resume",
            meta=None,
            lifespan_context=runtime,
        ),
        session=SimpleNamespace(client_params=None),
        transport="streamable-http",
    )
    async with request_context_scope(ctx, args.session_id, allow_pwd_bootstrap=False) as request_context:
        assert request_context.session is session
        assert request_context.session.project_is_bound is True
