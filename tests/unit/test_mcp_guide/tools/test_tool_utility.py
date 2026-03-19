"""Tests for utility tools."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.agent_detection import AgentInfo
from mcp_guide.guide import GuideMCP
from mcp_guide.tools.tool_utility import GetClientInfoArgs, client_info


def _make_ctx(agent_info=None, client_params=None):
    """Build a mock context with a mock session."""
    session = Mock()
    session.agent_info = agent_info
    session.client_params = client_params

    ctx = Mock()
    ctx.fastmcp = GuideMCP(name="test-server")
    ctx.session = session

    return ctx, session


@pytest.mark.anyio
async def test_client_info_no_cache():
    """Test client_info detects agent info when session has none."""
    ctx, session = _make_ctx(
        agent_info=None,
        client_params={"clientInfo": {"name": "Kiro CLI", "version": "1.0.0"}},
    )

    with patch("mcp_guide.session.get_session", new=AsyncMock(return_value=session)):
        result_str = await client_info(args=GetClientInfoArgs(), ctx=ctx)

    result = json.loads(result_str)

    assert result["success"] is True
    assert result["value"]["agent"] == "Kiro CLI"
    assert result["value"]["normalized_name"] == "kiro"
    assert result["value"]["version"] == "1.0.0"
    assert result["value"]["command_prefix"] == "@"
    assert "Kiro CLI" in result["message"]

    from mcp_guide.result_constants import INSTRUCTION_DISPLAY_ONLY

    assert result["instruction"] == INSTRUCTION_DISPLAY_ONLY

    # Verify agent_info stored on session
    assert session.agent_info is not None
    assert session.agent_info.name == "Kiro CLI"


@pytest.mark.anyio
async def test_client_info_with_cache():
    """Test client_info returns session-cached agent info."""
    cached = AgentInfo(name="Cached Agent", normalized_name="cached", version="2.0.0", prompt_prefix="/")
    ctx, session = _make_ctx(
        agent_info=cached,
        client_params={"clientInfo": {"name": "Different Agent", "version": "3.0.0"}},
    )

    with patch("mcp_guide.session.get_session", new=AsyncMock(return_value=session)):
        result_str = await client_info(args=GetClientInfoArgs(), ctx=ctx)

    result = json.loads(result_str)

    assert result["success"] is True
    assert result["value"]["agent"] == "Cached Agent"
    assert result["value"]["version"] == "2.0.0"
    assert "Different Agent" not in result["message"]


@pytest.mark.anyio
async def test_client_info_no_client_params():
    """Test client_info handles missing client_params."""
    ctx, session = _make_ctx(agent_info=None, client_params=None)

    with patch("mcp_guide.session.get_session", new=AsyncMock(return_value=session)):
        result_str = await client_info(args=GetClientInfoArgs(), ctx=ctx)

    result = json.loads(result_str)

    assert result["success"] is False
    assert "No client information available" in result["error"]


@pytest.mark.anyio
async def test_client_info_no_context():
    """Test client_info handles missing context."""
    result_str = await client_info(args=GetClientInfoArgs(), ctx=None)
    result = json.loads(result_str)

    assert result["success"] is False
    assert "Context not available" in result["error"]


@pytest.mark.anyio
async def test_client_info_wrong_server_type():
    """Test client_info handles non-GuideMCP server."""
    ctx = Mock()
    ctx.fastmcp = object()  # Not a GuideMCP instance
    ctx.session = Mock()

    result_str = await client_info(args=GetClientInfoArgs(), ctx=ctx)
    result = json.loads(result_str)

    assert result["success"] is False
    assert "Server must be GuideMCP instance" in result["error"]


@pytest.mark.anyio
async def test_client_info_dict_without_client_info():
    """Test client_info with dict missing clientInfo."""
    ctx, session = _make_ctx(agent_info=None, client_params={})

    with patch("mcp_guide.session.get_session", new=AsyncMock(return_value=session)):
        result_str = await client_info(args=GetClientInfoArgs(), ctx=ctx)

    result = json.loads(result_str)

    assert result["success"] is True
    assert result["value"]["agent"] == "Unknown"
    assert result["value"]["normalized_name"] == "unknown"
    assert result["value"]["command_prefix"] == "/"


@pytest.mark.anyio
async def test_client_info_pydantic_client_params():
    """Test client_info normalizes BaseModel client_params to a dict."""
    from pydantic import BaseModel

    class FakeClientParams(BaseModel):
        clientInfo: dict = {"name": "Kiro CLI", "version": "1.0.0"}

    ctx, session = _make_ctx(agent_info=None, client_params=FakeClientParams())

    with patch("mcp_guide.session.get_session", new=AsyncMock(return_value=session)):
        result_str = await client_info(args=GetClientInfoArgs(), ctx=ctx)

    result = json.loads(result_str)

    assert result["success"] is True
    assert result["value"]["agent"] == "Kiro CLI"
    # session.client_params must be a plain dict (JSON-serializable)
    assert isinstance(session.client_params, dict)
    assert session.client_params == {"clientInfo": {"name": "Kiro CLI", "version": "1.0.0"}}
