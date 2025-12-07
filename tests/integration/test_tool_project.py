"""Integration test for project management tool registration.

This test verifies that tool_project is properly registered with the MCP server.
For functional tests of the tool logic, see tests/unit/test_mcp_guide/tools/test_tool_project.py
"""

import pytest


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory):
    """Create fresh MCP server for this test module."""
    return mcp_server_factory(["tool_project"])


@pytest.mark.anyio
async def test_get_current_project_registered(mcp_server):
    """Test that get_current_project is registered in MCP."""
    tools = await mcp_server.list_tools()
    tool_names = [tool.name for tool in tools]

    assert "get_current_project" in tool_names
