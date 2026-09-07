"""Integration tests for utility tools."""

import json

import pytest
from fastmcp.client import Client, FastMCPTransport

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


@pytest.mark.anyio
async def test_client_info_returns_consistent_agent_info_without_project(mcp_server):
    """Test that client_info returns agent information from MCP client."""
    async with Client(FastMCPTransport(mcp_server, raise_exceptions=True)) as client:
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

        repeated = await call_mcp_tool(client, "client_info", args)
        repeated_data = json.loads(repeated.content[0].text)
        assert repeated_data["success"] is True
        assert repeated_data["message"] == message
        assert repeated_data["value"] == value
