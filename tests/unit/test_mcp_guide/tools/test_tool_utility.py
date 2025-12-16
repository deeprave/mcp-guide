"""Tests for utility tools."""

import json
from unittest.mock import Mock

import pytest

from mcp_guide.agent_detection import AgentInfo
from mcp_guide.guide import GuideMCP
from mcp_guide.tools.tool_utility import GetClientInfoArgs, client_info


@pytest.mark.asyncio
async def test_client_info_no_cache():
    """Test client_info detects and caches agent info."""
    # Create mock context
    ctx = Mock()
    ctx.fastmcp = GuideMCP(name="test-server")
    ctx.fastmcp.agent_info = None
    ctx.session = Mock()
    ctx.session.client_params = {"clientInfo": {"name": "Kiro CLI", "version": "1.0.0"}}

    result_str = await client_info(args=GetClientInfoArgs(), ctx=ctx)
    result = json.loads(result_str)

    assert result["success"] is True

    # Check structured data in value
    assert result["value"]["agent"] == "Kiro CLI"
    assert result["value"]["normalized_name"] == "kiro"
    assert result["value"]["version"] == "1.0.0"
    assert result["value"]["command_prefix"] == "@"

    # Check markdown in message
    assert "Kiro CLI" in result["message"]
    assert "kiro" in result["message"]
    assert "@" in result["message"]

    assert result["instruction"] == "Display this information to the user."

    # Verify caching
    assert ctx.fastmcp.agent_info is not None
    assert ctx.fastmcp.agent_info.name == "Kiro CLI"


@pytest.mark.asyncio
async def test_client_info_with_cache():
    """Test client_info returns cached agent info."""
    # Create mock context with cached agent info
    ctx = Mock()
    ctx.fastmcp = GuideMCP(name="test-server")
    ctx.fastmcp.agent_info = AgentInfo(
        name="Cached Agent", normalized_name="cached", version="2.0.0", prompt_prefix="/"
    )
    ctx.session = Mock()
    ctx.session.client_params = {"clientInfo": {"name": "Different Agent", "version": "3.0.0"}}

    result_str = await client_info(args=GetClientInfoArgs(), ctx=ctx)
    result = json.loads(result_str)

    assert result["success"] is True
    assert result["value"]["agent"] == "Cached Agent"
    assert result["value"]["version"] == "2.0.0"
    # Should use cached, not detect new agent
    assert "Different Agent" not in result["message"]


@pytest.mark.asyncio
async def test_client_info_no_client_params():
    """Test client_info handles missing client_params."""
    ctx = Mock()
    ctx.fastmcp = GuideMCP(name="test-server")
    ctx.fastmcp.agent_info = None
    ctx.session = Mock()
    ctx.session.client_params = None

    result_str = await client_info(args=GetClientInfoArgs(), ctx=ctx)
    result = json.loads(result_str)

    assert result["success"] is False
    assert "No client information available" in result["error"]


@pytest.mark.asyncio
async def test_client_info_no_context():
    """Test client_info handles missing context."""
    result_str = await client_info(args=GetClientInfoArgs(), ctx=None)
    result = json.loads(result_str)

    assert result["success"] is False
    assert "Context not available" in result["error"]


@pytest.mark.asyncio
async def test_client_info_wrong_server_type():
    """Test client_info handles non-GuideMCP server."""
    ctx = Mock()
    ctx.fastmcp = object()  # Not a GuideMCP instance
    ctx.session = Mock()

    result_str = await client_info(args=GetClientInfoArgs(), ctx=ctx)
    result = json.loads(result_str)

    assert result["success"] is False
    assert "Server must be GuideMCP instance" in result["error"]


@pytest.mark.asyncio
async def test_client_info_dict_without_client_info():
    """Test client_info with dict missing clientInfo."""
    ctx = Mock()
    ctx.fastmcp = GuideMCP(name="test-server")
    ctx.fastmcp.agent_info = None
    ctx.session = Mock()
    ctx.session.client_params = {}  # Empty dict, no clientInfo

    result_str = await client_info(args=GetClientInfoArgs(), ctx=ctx)
    result = json.loads(result_str)

    assert result["success"] is True
    assert result["value"]["agent"] == "Unknown"
    assert result["value"]["normalized_name"] == "unknown"
    assert result["value"]["command_prefix"] == "/"
