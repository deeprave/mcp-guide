"""Prompt routing uses real content, templates and explicit request contexts."""

import json
from types import SimpleNamespace

import pytest

from mcp_guide.models import Category
from mcp_guide.prompts.guide_prompt import guide
from mcp_guide.result_constants import INSTRUCTION_DISPLAY_ONLY, INSTRUCTION_ERROR_MESSAGE


async def invoke(context, *args, **kwargs):
    result = await guide.__wrapped__(*args, request_context=context, **kwargs)
    return json.loads(result.messages[0].content.text)


@pytest.mark.anyio
async def test_known_session_prompt_uses_its_content_without_minting(resource_project, monkeypatch):
    from mcp_guide.runtime import OwnerKey, get_runtime
    from mcp_guide.session import bind_session_project

    runtime = get_runtime()
    session = runtime.resolve_session(OwnerKey("known-session"))
    await bind_session_project(session, resource_project.session.bound_root_path)
    # The public boundary must resolve this exact session, not create another.
    session.session_id = "known-session"

    def cannot_mint(*args, **kwargs):
        raise AssertionError("Known session must not mint")

    monkeypatch.setattr(runtime, "create_session", cannot_mint)
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(
            protocol_version="2026-07-28", request_id="prompt", meta=None, lifespan_context=runtime
        ),
        session=SimpleNamespace(client_params=None),
        transport="streamable-http",
    )
    result = await guide("docs", session_id="known-session", ctx=ctx)
    payload = json.loads(result.messages[0].content.text)
    assert payload["success"]
    assert "docs content" in payload["value"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "args,override,expected",
    [
        ((), None, "@guide :help"),
        (("",), "g", "@g :help"),
        ((":",), None, "Command name cannot be empty"),
        ((";",), None, "Command name cannot be empty"),
    ],
)
async def test_empty_prompt_and_command_errors(resource_project, monkeypatch, args, override, expected):
    if override:
        monkeypatch.setenv("MCP_PROMPT_NAME", override)
    result = await invoke(resource_project, *args)
    assert not result["success"]
    assert result["error_type"] == "validation_error"
    assert expected in result["error"]
    assert result["instruction"] == INSTRUCTION_ERROR_MESSAGE


@pytest.mark.anyio
@pytest.mark.parametrize(
    "args,kwargs,names",
    [
        (("docs",), {"arg3": "policies"}, ["docs"]),
        (("docs",), {"arg2": "policies"}, ["docs", "policies"]),
        (("docs/readme,policies/git/ops/*", "extra"), {}, ["docs", "policies", "extra"]),
        (tuple(f"cat{i}" for i in range(15)), {}, [f"cat{i}" for i in range(15)]),
    ],
    ids=["first-omission", "ordering", "mixed-expressions", "fifteen-arguments"],
)
async def test_argument_routing_returns_requested_content(resource_project, args, kwargs, names):
    session = resource_project.session
    for name in names:
        if name in {"docs", "policies"}:
            continue
        folder = resource_project.resolve_document_path(name)
        folder.mkdir()
        (folder / "readme.md").write_text(f"Unique {name} content")
        await session.update_config(lambda p, name=name: p.with_category(name, Category(dir=name, patterns=["*.md"])))
    result = await invoke(resource_project, *args, **kwargs)
    assert result["success"], result
    body = result["value"]
    previous = -1
    for name in names:
        text = {"docs": "docs content", "policies": "git policy"}.get(name, f"Unique {name} content")
        position = body.index(text)
        assert position > previous
        previous = position
    if names == ["docs"]:
        assert "git policy" not in body
    assert result["instruction"].startswith(INSTRUCTION_DISPLAY_ONLY)


@pytest.mark.anyio
async def test_empty_content_and_template_error(resource_project):
    resource_project.resolve_document_path("docs/readme.md").write_text("")
    empty = await invoke(resource_project, "docs")
    assert empty["success"]
    assert empty["value"] == ""
    assert empty["instruction"].startswith(INSTRUCTION_DISPLAY_ONLY)
    command = resource_project.resolve_document_path("_commands/error.mustache")
    command.write_text("{{#_error}}Missing required argument: name{{/_error}}")
    error = await invoke(resource_project, ":error")
    assert not error["success"]
    assert error["error_type"] == "validation_error"
    assert error["error_data"]["errors"] == ["Missing required argument: name"]
