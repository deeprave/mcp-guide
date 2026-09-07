"""Resource URI routing through real project content and command templates."""

import pytest

from mcp_guide.tools.tool_resource import ReadResourceArgs, internal_read_resource


@pytest.mark.anyio
@pytest.mark.parametrize(
    "uri,expected",
    [
        ("guide://docs", "docs content"),
        ("guide://docs/readme", "docs content"),
        ("guide://_project", "resource-project verbose"),
        ("guide://_openspec/show/my-change?verbose=true", "Show my-change verbose"),
        ("guide://_project?table=true", "resource-project verbose table"),
    ],
)
async def test_resource_uri_renders_the_bound_projects_content(resource_project, uri, expected):
    result = await internal_read_resource(ReadResourceArgs(uri=uri), resource_project)
    assert result.success, result.error
    assert result.value == expected


@pytest.mark.anyio
async def test_invalid_scheme(resource_project):
    result = await internal_read_resource(ReadResourceArgs(uri="http://example.com"), resource_project)
    assert result.success is False
    assert result.error_type == "validation_error"
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
