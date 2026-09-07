"""Conversion from Guide results to FastMCP's public response types."""

from __future__ import annotations

import json
from typing import Any

from fastmcp.prompts import PromptResult
from fastmcp.resources import ResourceResult
from fastmcp.tools.base import ToolResult
from mcp_types import TextContent

from mcp_guide.core.result import Result
from mcp_guide.mcp_context import SessionProtocolType

SESSION_CONTINUATION_INSTRUCTION = (
    "In future requests, provide session_id unchanged in tools and prompts. "
    "Add session_id unchanged as a query argument to resource URIs."
)


def add_session_continuation(payload: dict[str, Any], session_id: str | None) -> dict[str, Any]:
    """Attach modern-client session continuation details to a successful payload."""
    if session_id is None or not payload.get("success", False):
        return payload

    payload = {**payload, "session_id": session_id}
    instruction = payload.get("instruction")
    if not (isinstance(instruction, str) and instruction.endswith(SESSION_CONTINUATION_INSTRUCTION)):
        payload["instruction"] = (
            f"{instruction}\n\n{SESSION_CONTINUATION_INSTRUCTION}" if instruction else SESSION_CONTINUATION_INSTRUCTION
        )
    return payload


def _response_payload_and_metadata(
    result: Result[Any],
    *,
    session_id: str | None,
    protocol_type: SessionProtocolType | None,
) -> tuple[dict[str, Any], dict[str, dict[str, str]] | None]:
    """Adapt a Result according to the established Session response contract."""
    payload = add_session_continuation(result.to_json(), session_id)
    if protocol_type is not SessionProtocolType.MCP_2026_07_28:
        return payload, None
    instruction = payload.pop("additional_agent_instructions", None)
    return payload, {"mcp-guide": {"instructions": instruction}} if instruction else None


def tool_response(
    result: Result[Any], *, session_id: str | None = None, protocol_type: SessionProtocolType | None = None
) -> ToolResult:
    """Return a native FastMCP result without dropping Guide result fields.

    The structured payload is the canonical Guide result representation. The
    matching text block retains compatibility with clients that only render
    text content.
    """
    payload, meta = _response_payload_and_metadata(result, session_id=session_id, protocol_type=protocol_type)
    return ToolResult(
        content=[TextContent(type="text", text=json.dumps(payload))],
        structured_content=payload,
        meta=meta,
        is_error=not result.success,
    )


def prompt_response(
    result: Result[Any], *, session_id: str | None = None, protocol_type: SessionProtocolType | None = None
) -> PromptResult:
    """Return a native FastMCP prompt response without discarding Guide data.

    Prompt results carry the canonical Guide payload as their message body.
    """
    payload, meta = _response_payload_and_metadata(result, session_id=session_id, protocol_type=protocol_type)
    return PromptResult(json.dumps(payload), meta=meta)


def resource_response(
    result: Result[Any], *, session_id: str | None = None, protocol_type: SessionProtocolType | None = None
) -> ResourceResult:
    """Return a native FastMCP resource result preserving the Guide payload."""
    payload, meta = _response_payload_and_metadata(result, session_id=session_id, protocol_type=protocol_type)
    return ResourceResult(json.dumps(payload), meta=meta)


__all__ = ["prompt_response", "resource_response", "tool_response"]
