"""Regression coverage for native Guide MCP public-surface adapters."""

from unittest.mock import AsyncMock, patch

import pytest
from fastmcp.prompts import PromptResult
from fastmcp.tools.base import ToolResult

from mcp_guide.result import Result
from mcp_guide.tools.tool_resource import session_id_from_guide_uri
from mcp_guide.tools.tool_result import prompt_result, tool_result


def _rich_result() -> Result[str]:
    return Result.ok(
        "rendered guide content",
        instruction="Read before continuing.",
        disposition="agent/instruction",
        additional_agent_instructions="Use only the bound project.",
    )


@pytest.mark.anyio
async def test_tool_and_prompt_boundaries_preserve_agent_directed_result_fields() -> None:
    """Tools and prompts use their native FastMCP responses without text-only loss."""
    tool = await tool_result("surface-test", _rich_result())
    prompt = await prompt_result("surface-test", _rich_result())

    assert isinstance(tool, ToolResult)
    assert tool.structured_content is not None
    assert tool.structured_content["instruction"] == "Read before continuing."
    assert tool.structured_content["disposition"] == "agent/instruction"
    assert tool.structured_content["additional_agent_instructions"] == "Use only the bound project."

    assert isinstance(prompt, PromptResult)
    import json

    prompt_payload = json.loads(prompt.messages[0].content.text)
    assert prompt_payload["instruction"] == "Read before continuing."
    assert prompt_payload["disposition"] == "agent/instruction"
    assert prompt_payload["additional_agent_instructions"] == "Use only the bound project."


@pytest.mark.anyio
async def test_resource_boundary_preserves_agent_directed_result_fields() -> None:
    """Native resources preserve Guide result semantics in their metadata."""
    from mcp_guide.resources import guide_resource

    session = type(
        "Session",
        (),
        {
            "session_id": "bound-session",
            "task_manager": type("Tasks", (), {"process_result": AsyncMock(side_effect=lambda r: r)})(),
        },
    )()
    get_session = AsyncMock(return_value=session)
    with (
        patch("mcp_guide.resources.get_session", get_session),
        patch("mcp_guide.resources.internal_get_content", new=AsyncMock(return_value=_rich_result())),
    ):
        resource = await guide_resource("docs", "overview", session_id="bound-session")

    get_session.assert_awaited_once()
    assert get_session.await_args.kwargs["session_id"] == "bound-session"

    # Direct Python calls retain their historical JSON surface; FastMCP wraps
    # this as a ResourceResult only at resource dispatch.
    import json

    payload = json.loads(resource)
    assert payload["instruction"].startswith("Read before continuing.")
    assert payload["session_id"] == "bound-session"
    assert payload["disposition"] == "agent/instruction"
    assert payload["additional_agent_instructions"] == "Use only the bound project."


@pytest.mark.parametrize(
    ("uri", "expected"),
    [
        ("guide://docs/overview?session_id=bound-session", "bound-session"),
        ("guide://docs/overview", None),
        ("guide://docs/overview?session_id=", ""),
    ],
)
def test_resource_uri_extracts_the_opaque_session_id(uri: str, expected: str | None) -> None:
    """URI resources use the same opaque session-id value as tool arguments."""
    assert session_id_from_guide_uri(uri) == expected


def test_resource_uri_rejects_ambiguous_session_ids() -> None:
    """A resource URI cannot select an interaction through repeated values."""
    with pytest.raises(ValueError, match="at most one"):
        session_id_from_guide_uri("guide://docs/overview?session_id=one&session_id=two")
