"""Regression coverage for native Guide MCP public-surface adapters."""

from types import SimpleNamespace

import pytest
from fastmcp.prompts import PromptResult
from fastmcp.tools.base import ToolResult

from mcp_guide.mcp_context import SessionProtocolType
from mcp_guide.result import Result
from mcp_guide.tools.tool_project import SwitchProjectArgs, switch_project
from mcp_guide.tools.tool_resource import session_id_from_guide_uri
from mcp_guide.tools.tool_result import prompt_result, tool_result


def _rich_result() -> Result[str]:
    return Result.ok(
        "rendered guide content",
        instruction="Read before continuing.",
        disposition="agent/instruction",
        additional_agent_instructions="Use only the bound project.",
    )


async def _drain_pending_instructions(session) -> None:
    """Remove setup-task instructions before asserting a deliberately supplied result."""
    for _ in range(10):
        if (await session.task_manager.process_result(Result.ok())).additional_agent_instructions is None:
            return
    raise AssertionError("Session setup instructions did not drain after 10 results")


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
async def test_modern_tool_and_prompt_boundaries_use_response_metadata(task_manager) -> None:
    """Modern Session protocol type reaches both non-resource response adapters."""
    import json

    import mcp_guide.mcp_instruction_notifications as notification_module

    class NonNegotiatingMcpContext:
        def client_extension_settings(self, _identifier: str) -> None:
            return None

        def client_supports_extension(self, _identifier: str) -> bool:
            return False

    session = SimpleNamespace(
        session_id="modern-surface",
        protocol_type=SessionProtocolType.MCP_2026_07_28,
        task_manager=task_manager,
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(notification_module, "get_context", NonNegotiatingMcpContext)
        tool = await tool_result("surface-test", _rich_result(), session=session)
        prompt = await prompt_result("surface-test", _rich_result(), session=session)

    assert tool.meta == {"mcp-guide": {"instructions": "Use only the bound project."}}
    assert "additional_agent_instructions" not in tool.structured_content
    assert prompt.meta == {"mcp-guide": {"instructions": "Use only the bound project."}}
    assert "additional_agent_instructions" not in json.loads(prompt.messages[0].content.text)


@pytest.mark.anyio
async def test_switch_project_uses_modern_response_metadata(task_manager, monkeypatch) -> None:
    """A modern switch response moves queued guidance into its metadata."""
    session = SimpleNamespace(
        session_id="modern-switch",
        protocol_type=SessionProtocolType.MCP_2026_07_28,
        task_manager=task_manager,
    )
    context = SimpleNamespace(session=session, session_id="bound-session")

    async def switch_with_guidance(_args, _request_context):
        return _rich_result(), session

    monkeypatch.setattr("mcp_guide.tools.tool_project._switch_project_result", switch_with_guidance)
    import mcp_guide.mcp_instruction_notifications as notification_module

    class NonNegotiatingMcpContext:
        def client_extension_settings(self, _identifier: str) -> None:
            return None

        def client_supports_extension(self, _identifier: str) -> bool:
            return False

    monkeypatch.setattr(notification_module, "get_context", NonNegotiatingMcpContext)
    response = await switch_project.__wrapped__(SwitchProjectArgs(name="review"), request_context=context)

    assert response.meta == {"mcp-guide": {"instructions": "Use only the bound project."}}
    assert "additional_agent_instructions" not in response.structured_content


@pytest.mark.anyio
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


def test_read_resource_args_copy_unique_uri_session_id() -> None:
    """The tool field receives a unique URI session_id when it is absent."""
    from mcp_guide.tools.tool_resource import ReadResourceArgs

    args = ReadResourceArgs(uri="guide://docs/overview?session_id=bound-session")
    assert args.session_id == "bound-session"


def test_read_resource_args_keep_explicit_session_id() -> None:
    """An explicit tool session_id is not overwritten by the URI query."""
    from mcp_guide.tools.tool_resource import ReadResourceArgs

    args = ReadResourceArgs(uri="guide://docs/overview?session_id=from-uri", session_id="from-field")
    assert args.session_id == "from-field"


def test_read_resource_args_reject_empty_uri_session_id() -> None:
    """An empty URI session_id is rejected before request scope."""
    from pydantic import ValidationError

    from mcp_guide.tools.tool_resource import ReadResourceArgs

    with pytest.raises(ValidationError):
        ReadResourceArgs(uri="guide://docs/overview?session_id=")
