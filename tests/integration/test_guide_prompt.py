"""Prompt routing uses real content, templates and explicit request contexts."""

import json

import pytest
from mcp_types import InputRequiredResult

from mcp_guide.prompts import guide_prompt
from mcp_guide.prompts.guide_prompt import guide


async def invoke(context, *args, **kwargs):
    result = await guide.__wrapped__(*args, request_context=context, **kwargs)
    return json.loads(result.messages[0].content.text)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "args,override,expected,expected_disposition",
    [
        ((), None, "@guide :help", None),
        (("",), "g", "@g :help", None),
        ((":",), None, "Command name cannot be empty", "agent/error"),
        ((";",), None, "Command name cannot be empty", "agent/error"),
    ],
)
async def test_empty_prompt_and_command_errors(
    resource_project, monkeypatch, args, override, expected, expected_disposition
):
    if override:
        monkeypatch.setenv("MCP_PROMPT_NAME", override)
    result = await invoke(resource_project, *args)
    assert not result["success"]
    assert result["error_type"] == "validation_error"
    assert expected in result["error"]
    assert result.get("disposition") == expected_disposition


@pytest.mark.anyio
@pytest.mark.anyio
async def test_command_request_rejects_unsafe_path(resource_project):
    result = await invoke(resource_project, ":../../../etc/passwd")
    assert not result["success"]
    assert result["error_type"] == "security_error"
    assert result["disposition"] == "agent/error"


@pytest.mark.anyio
async def test_content_request_rejects_malformed_flag(resource_project):
    result = await invoke(resource_project, "docs", "--pattern=x", "--")
    assert not result["success"]
    assert result["error_type"] == "validation_error"
    assert result["disposition"] == "agent/error"
    assert "flag parsing failed" in result["error"].lower()


@pytest.mark.anyio
async def test_content_request_rejects_a_single_malformed_flag(resource_project):
    """A lone malformed flag must not be silently skipped as if it were a command name."""
    result = await invoke(resource_project, "docs", "--")
    assert not result["success"]
    assert result["error_type"] == "validation_error"
    assert result["disposition"] == "agent/error"
    assert "flag parsing failed" in result["error"].lower()


@pytest.mark.anyio
async def test_prompt_preserves_an_input_request(resource_project, monkeypatch):
    """Prompts preserve modern MCP input requests for a retry."""

    async def requires_input(*_args, **_kwargs):
        return InputRequiredResult(input_requests={}, request_state="skill-elicitation")

    from mcp_guide.tools import tool_resource

    monkeypatch.setattr(tool_resource, "internal_read_resource", requires_input)

    result = await guide_prompt._handle_uri_namespace_request(["guide", "$guide-review"], resource_project)

    assert isinstance(result, InputRequiredResult)


@pytest.mark.anyio
async def test_prompt_returns_structured_not_found_for_an_unknown_skill_member(resource_project):
    """A missing skill member follows the ordinary Guide prompt error contract."""
    result = await invoke(resource_project, "$status-snapshot/resources/missing.md")

    assert result["success"] is False
    assert result["error_type"] == "not_found"
