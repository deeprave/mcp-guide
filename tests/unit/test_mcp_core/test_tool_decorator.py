"""Tests for the tool decorator's public error boundaries."""

from types import SimpleNamespace

import pytest


@pytest.mark.anyio
async def test_unbound_request_context_returns_no_project_response() -> None:
    """An explicitly unbound application context receives the standard result."""
    from mcp_guide.core.tool_decorator import _check_project_bound

    response = await _check_project_bound(SimpleNamespace(is_bound=False))

    assert response is not None
    assert response.structured_content["error_type"] == "no_project"


def test_invalid_session_result_includes_rebind_guidance() -> None:
    """A rejected session ID tells the agent to discard it and call set_project."""
    from mcp_guide.mcp_result_adapter import tool_response
    from mcp_guide.result_constants import make_invalid_session_result

    response = tool_response(make_invalid_session_result())

    assert response.structured_content is not None
    assert response.structured_content["error_type"] == "invalid_session"
    instruction = response.structured_content["instruction"]
    assert "discard" in instruction.lower()
    assert "set_project" in instruction


def test_unmintable_session_result_is_a_project_error() -> None:
    """An unmintable client receives an in-band project error, not a transport failure."""
    from mcp_guide.mcp_result_adapter import tool_response
    from mcp_guide.result_constants import make_unmintable_session_result

    response = tool_response(make_unmintable_session_result())

    assert response.structured_content is not None
    assert response.structured_content["error_type"] == "project_error"
    assert "cannot carry a Guide session" in response.structured_content["error"]
    assert "2026-07-28" in response.structured_content["instruction"]
