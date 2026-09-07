"""Regression coverage for native Guide MCP public-surface adapters."""

from dataclasses import replace

import pytest
import yaml
from fastmcp.prompts import PromptResult
from fastmcp.tools.base import ToolResult
from tests.helpers import create_bound_test_session, request_context_for

from mcp_guide.models import Category
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
async def test_resource_boundary_preserves_agent_directed_result_fields(runtime, tmp_path) -> None:
    """Rendered file guidance and queued instructions reach the native resource payload."""
    import json

    from mcp_guide.resources import guide_resource

    docroot = tmp_path / "docs"
    content_dir = docroot / "guidance"
    content_dir.mkdir(parents=True)
    (content_dir / "overview.mustache").write_text(
        "---\ntype: agent/instruction\ninstruction: Read before continuing.\n---\nrendered guide content"
    )
    config = runtime.configuration_service().config_file
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {}}))
    session = await create_bound_test_session(runtime, "surface")
    await session.update_config(
        lambda project: replace(project, categories={"docs": Category(name="docs", dir="guidance", patterns=["*"])})
    )
    await session.task_manager.queue_instruction("Use only the bound project.")
    context = await request_context_for(session, "bound-session")
    resource = await guide_resource.__wrapped__(
        "docs", "overview", session_id="bound-session", request_context=context, request_uri=None
    )
    payload = json.loads(resource.contents[0].content)
    assert payload["success"] is True
    assert payload["value"] == "rendered guide content"
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
