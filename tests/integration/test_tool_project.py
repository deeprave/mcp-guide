"""Integration test for project management tool registration.

This test verifies that tool_project is properly registered with the MCP server.
For functional tests of the tool logic, see tests/unit/test_mcp_guide/tools/test_tool_project.py
"""

import pytest


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


@pytest.mark.anyio
async def test_get_current_project_registered(mcp_server_factory):
    """Test that get_current_project is registered in MCP."""
    server = mcp_server_factory(["tool_project"])
    tools = await server.list_tools()
    tool_names = [tool.name for tool in tools]

    assert "get_current_project" in tool_names
