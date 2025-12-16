"""Integration tests for utility tools."""

import json
from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from mcp_guide.session import get_or_create_session, remove_current_session
from mcp_guide.tools.tool_utility import GetClientInfoArgs
from tests.conftest import call_mcp_tool


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory):
    """Create fresh MCP server for this test module."""
    return mcp_server_factory(["tool_utility"])


@pytest.fixture
async def test_session(tmp_path: Path):
    """Create test session with isolated config."""
    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    yield session
    remove_current_session("test")


@pytest.mark.anyio
async def test_client_info_returns_agent_info(mcp_server, test_session):
    """Test that client_info returns agent information from MCP client."""
    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = GetClientInfoArgs()
        result = await call_mcp_tool(client, "client_info", args)

        # Parse result
        assert result.content is not None
        assert len(result.content) > 0

        content = result.content[0]
        assert hasattr(content, "text")

        result_data = json.loads(content.text)  # type: ignore[union-attr]

        # Verify successful response
        assert result_data["success"] is True
        assert "value" in result_data
        assert "message" in result_data

        # Verify value schema
        value = result_data["value"]
        assert "agent" in value
        assert "normalized_name" in value
        assert "command_prefix" in value

        # Verify message formatting (AU/UK spelling)
        message = result_data["message"]
        assert "Normalised Name:" in message
        assert "Agent:" in message or "Client" in message


@pytest.mark.anyio
async def test_client_info_caches_agent_info(mcp_server, test_session):
    """Test that client_info caches agent info across multiple calls."""
    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = GetClientInfoArgs()

        # First call
        result1 = await call_mcp_tool(client, "client_info", args)
        content1 = result1.content[0]
        data1 = json.loads(content1.text)  # type: ignore[union-attr]

        # Second call
        result2 = await call_mcp_tool(client, "client_info", args)
        content2 = result2.content[0]
        data2 = json.loads(content2.text)  # type: ignore[union-attr]

        # Both calls must succeed to exercise cache path
        assert data1["success"] is True
        assert data2["success"] is True

        # Cached responses must be identical
        assert data1["message"] == data2["message"]
        assert data1["value"] == data2["value"]
