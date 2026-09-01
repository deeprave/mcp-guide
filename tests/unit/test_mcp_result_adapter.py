"""Unit tests for the FastMCP result boundary."""

import json

from mcp_guide.mcp_result_adapter import prompt_response, resource_response, tool_response
from mcp_guide.result import Result

SESSION_CONTINUATION_INSTRUCTION = (
    "In future requests, provide session_id unchanged in tools and prompts. "
    "Add session_id unchanged as a query argument to resource URIs."
)


def test_tool_response_preserves_guide_instructions_and_disposition() -> None:
    """SDK conversion carries all agent-directed fields in structured content."""
    result = Result.ok(
        {"answer": 42},
        instruction="Read this before continuing.",
        disposition="agent/instruction",
        additional_agent_instructions="Use the bound project only.",
    )

    response = tool_response(result)

    assert response.is_error is False
    assert response.structured_content is not None
    assert response.structured_content["instruction"] == "Read this before continuing."
    assert response.structured_content["disposition"] == "agent/instruction"
    assert response.structured_content["additional_agent_instructions"] == "Use the bound project only."
    assert response.meta is None


def test_tool_response_marks_guide_failures_as_native_errors() -> None:
    """A Guide failure becomes a protocol-level tool error while retaining details."""
    result = Result.failure("Cannot continue", error_type="no_project")
    response = tool_response(result)

    assert response.is_error is True
    assert response.structured_content == result.to_json()


def test_prompt_response_serialises_the_guide_result() -> None:
    """Prompt results retain the same agent-directed payload as tools/resources."""
    result = Result.ok(
        "Rendered command",
        instruction="Follow the command guidance.",
        disposition="agent/instruction",
        additional_agent_instructions="Stay within the bound project.",
    )

    response = prompt_response(result)

    assert response.meta is None


def test_resource_response_serialises_the_guide_result() -> None:
    """Resources use FastMCP's resource result type, not a tool result."""
    result = Result.failure("Document is unavailable", error_type="not_found")

    response = resource_response(result)

    assert response.meta is None


def test_tool_response_explains_how_to_continue_a_session() -> None:
    """A successful tool result tells modern clients how to replay its session."""
    response = tool_response(Result.ok("bound"), session_id="session-123")

    assert response.structured_content == {
        "success": True,
        "value": "bound",
        "instruction": f"{Result.default_success_instruction}\n\n{SESSION_CONTINUATION_INSTRUCTION}",
        "session_id": "session-123",
    }


def test_prompt_response_explains_how_to_continue_a_session() -> None:
    """A successful prompt result tells modern clients how to replay its session."""
    response = prompt_response(Result.ok("bound"), session_id="session-123")

    assert json.loads(response.messages[0].content.text) == {
        "success": True,
        "value": "bound",
        "instruction": f"{Result.default_success_instruction}\n\n{SESSION_CONTINUATION_INSTRUCTION}",
        "session_id": "session-123",
    }


def test_resource_response_explains_how_to_continue_a_session() -> None:
    """A successful resource result tells modern clients how to replay its session."""
    response = resource_response(Result.ok("bound"), session_id="session-123")

    assert json.loads(response.contents[0].content) == {
        "success": True,
        "value": "bound",
        "instruction": f"{Result.default_success_instruction}\n\n{SESSION_CONTINUATION_INSTRUCTION}",
        "session_id": "session-123",
    }
