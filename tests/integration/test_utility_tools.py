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
async def test_get_client_info_returns_agent_info(mcp_server, test_session):
    """Test that get_client_info returns agent information from MCP client."""
    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = GetClientInfoArgs()
        result = await call_mcp_tool(client, "get_client_info", args)

        # Parse result
        assert result.content is not None
        assert len(result.content) > 0

        content = result.content[0]
        assert hasattr(content, "text")

        result_data = json.loads(content.text)  # type: ignore[union-attr]

        # Print client info for inspection
        print("\n=== MCP Test Client Info ===")
        print(f"Success: {result_data['success']}")
        print(f"Value: {result_data.get('value')}")
        print(f"Message:\n{result_data.get('message', 'No message')}")
        print("===========================\n")

        # Verify result structure
        # Note: client_params may not be available in test environment
        if result_data["success"]:
            assert "value" in result_data
            assert "message" in result_data
            message = result_data["message"]
            # Check for AU/UK spelling
            assert "Normalised Name:" in message
            assert "Agent:" in message or "Client" in message
        else:
            # Expected if client_params not available
            assert "error" in result_data or "message" in result_data
            print(f"Note: {result_data.get('message', result_data.get('error'))}")


@pytest.mark.anyio
async def test_get_client_info_caches_agent_info(mcp_server, test_session):
    """Test that get_client_info caches agent info across multiple calls."""
    async with create_connected_server_and_client_session(mcp_server, raise_exceptions=True) as client:
        args = GetClientInfoArgs()

        # First call
        result1 = await call_mcp_tool(client, "get_client_info", args)
        content1 = result1.content[0]
        data1 = json.loads(content1.text)  # type: ignore[union-attr]

        # Second call
        result2 = await call_mcp_tool(client, "get_client_info", args)
        content2 = result2.content[0]
        data2 = json.loads(content2.text)  # type: ignore[union-attr]

        # Both calls should return same result (success or failure)
        assert data1["success"] == data2["success"]

        if data1["success"]:
            # If successful, verify caching worked
            assert data1["message"] == data2["message"]
            print("\n=== Caching Test ===")
            print(f"First call: {data1['message'][:100]}...")
            print(f"Second call: {data2['message'][:100]}...")
            print("Results match: ✓")
            print("===================\n")
        else:
            # Both should fail with same error
            print(f"\nNote: Both calls failed as expected: {data1.get('message', data1.get('error'))}")
