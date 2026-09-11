"""Native MCP result payloads preserve Guide semantics across all three surfaces."""

import json

import pytest

from mcp_guide.mcp_context import SessionProtocolType
from mcp_guide.mcp_result_adapter import prompt_response, resource_response, tool_response
from mcp_guide.render.cache_policy import CachePolicy
from mcp_guide.result import Result

SESSION_CONTINUATION_INSTRUCTION = (
    "In future requests, provide session_id unchanged in tools and prompts. "
    "Add session_id unchanged as a query argument to resource URIs."
)


@pytest.mark.parametrize(
    "adapter", [tool_response, prompt_response, resource_response], ids=["tool", "prompt", "resource"]
)
def test_native_adapter_preserves_rich_payload_errors_and_session_continuation(adapter):
    def payload(response):
        if adapter is tool_response:
            text_payload = json.loads(response.content[0].text)
            assert response.structured_content == text_payload
            return text_payload
        if adapter is prompt_response:
            return json.loads(response.messages[0].content.text)
        return json.loads(response.contents[0].content)

    result = Result.ok(
        {"answer": 42},
        instruction="Read before continuing.",
        disposition="agent/instruction",
        additional_agent_instructions="Use the bound project only.",
    )
    response = adapter(result)
    assert payload(response) == result.to_json()
    assert response.meta is None
    if adapter is tool_response:
        assert response.is_error is False

    failure = Result.failure("Cannot continue", error_type="no_project")
    failed = adapter(failure, session_id="session-123")
    assert payload(failed) == failure.to_json()  # Errors do not attach continuation.
    if adapter is tool_response:
        assert failed.is_error is True

    continued = payload(adapter(result, session_id="session-123"))
    assert continued == {
        **result.to_json(),
        "session_id": "session-123",
        "instruction": f"Read before continuing.\n\n{SESSION_CONTINUATION_INSTRUCTION}",
    }


@pytest.mark.parametrize(
    "adapter", [tool_response, prompt_response, resource_response], ids=["tool", "prompt", "resource"]
)
def test_modern_adapter_moves_agent_instruction_to_namespaced_metadata(adapter):
    """MCP 2026-07-28 uses response metadata without changing Result itself."""

    def payload(response):
        if adapter is tool_response:
            return response.structured_content
        if adapter is prompt_response:
            return json.loads(response.messages[0].content.text)
        return json.loads(response.contents[0].content)

    result = Result.ok("answer", additional_agent_instructions="Use the bound project only.")

    response = adapter(result, protocol_type=SessionProtocolType.MCP_2026_07_28)

    assert result.additional_agent_instructions == "Use the bound project only."
    assert payload(response)["success"] is True
    assert payload(response)["value"] == "answer"
    assert "additional_agent_instructions" not in payload(response)
    assert response.meta == {"mcp-guide": {"instructions": "Use the bound project only."}}


@pytest.mark.parametrize("adapter", [tool_response, resource_response], ids=["tool", "resource"])
def test_document_adapter_adds_explicit_cache_policy_to_namespaced_metadata(adapter):
    """Cache metadata comes only from the resolved document policy."""
    result = Result.ok("answer", cache_policy=CachePolicy.parse("medium, private")[0])

    response = adapter(result, protocol_type=SessionProtocolType.MCP_2026_07_28)

    assert response.meta == {"mcp-guide": {"cache": {"ttl_ms": 900_000, "scope": "private"}}}
