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
) -> tuple[dict[str, Any], dict[str, dict[str, Any]] | None]:
    """Adapt a Result according to the established Session response contract."""
    payload = add_session_continuation(result.to_json(), session_id)
    cache_metadata = result.cache_policy.metadata if result.cache_policy is not None else None
    if protocol_type is not SessionProtocolType.MCP_2026_07_28:
        return payload, {"mcp-guide": {"cache": cache_metadata}} if cache_metadata else None
    instruction = payload.pop("additional_agent_instructions", None)
    metadata = {key: value for key, value in {"instructions": instruction, "cache": cache_metadata}.items() if value}
    return payload, {"mcp-guide": metadata} if metadata else None


def tool_response(
    result: Result[Any], *, session_id: str | None = None, protocol_type: SessionProtocolType | None = None
) -> ToolResult:
    """Return a native FastMCP result using the Session response contract.

    Legacy sessions preserve the complete Guide payload. Modern sessions move
    ``additional_agent_instructions`` to ``_meta["mcp-guide"]["instructions"]``.
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
    """Return a native FastMCP prompt response using the Session response contract.

    Legacy prompts retain the complete Guide payload; modern prompts move
    ``additional_agent_instructions`` to response metadata.
    """
    payload, meta = _response_payload_and_metadata(result, session_id=session_id, protocol_type=protocol_type)
    return PromptResult(json.dumps(payload), meta=meta)


def resource_response(
    result: Result[Any], *, session_id: str | None = None, protocol_type: SessionProtocolType | None = None
) -> ResourceResult:
    """Return a native FastMCP resource result using the Session response contract.

    Legacy resources retain the complete Guide payload; modern resources move
    ``additional_agent_instructions`` to response metadata.
    """
    payload, meta = _response_payload_and_metadata(result, session_id=session_id, protocol_type=protocol_type)
    return ResourceResult(json.dumps(payload), meta=meta)


__all__ = ["prompt_response", "resource_response", "tool_response"]
