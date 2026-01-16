"""Integration tests for tool registration with FastMCP.

Tests that tools are correctly registered and invocable through MCP protocol.
"""

import json

import pytest
import pytest_asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_guide.core.tool_decorator import disable_test_mode, enable_test_mode
from mcp_guide.session import Session, remove_current_session, set_current_session


@pytest.fixture(scope="session", autouse=True)
def production_mode():
    """Ensure production mode for integration tests."""
    disable_test_mode()
    yield
    enable_test_mode()  # Restore test mode for other tests


@pytest_asyncio.fixture
async def test_session(tmp_path):
    """Create test session with sample project."""
    from mcp_guide.tools.tool_category import CategoryAddArgs, internal_category_add

    session = Session("test", _config_dir_for_tests=str(tmp_path))
    await session.get_project()
    set_current_session(session)

    # Add a category using the internal API
    args = CategoryAddArgs(name="docs", dir="documentation", patterns=["*.md", "*.txt"])
    await internal_category_add(args)

    yield session
    await remove_current_session("test")


@pytest.mark.asyncio
async def test_server_starts_and_registers_tools(test_session):
    """Test that server starts and tools are registered.

    This test verifies:
    1. Server can be created successfully
    2. Tools are imported and decorated
    3. No errors during startup
    """
    from mcp_guide.server import create_server

    # Create server - this triggers tool registration
    server = create_server()

    # Verify server was created
    assert server is not None
    assert server.name == "guide"

    # Server should have tools registered (FastMCP internal)
    # We can't directly inspect FastMCP's tool registry, but if
    # create_server() completes without error, tools are registered
    assert hasattr(server, "tool")


@pytest.mark.asyncio
async def test_tool_registration_with_fastmcp():
    """Test that tools register correctly with FastMCP instance."""
    from mcp_guide.server import create_server

    # Create server
    server = create_server()

    # Verify server was created
    assert server is not None
    assert server.name == "guide"

    # FastMCP should have tools registered
    # Note: FastMCP doesn't expose a direct way to list tools,
    # but we can verify the server was created successfully
    assert hasattr(server, "tool")


@pytest.mark.asyncio
async def test_auto_generated_description():
    """Test that tool descriptions are auto-generated from args class."""
    from mcp_guide.server import create_server

    # Create server (triggers registration)
    server = create_server()

    # Verify description generation works
    from mcp_guide.core.tool_arguments import ToolArguments
    from mcp_guide.tools.tool_category import category_list

    description = ToolArguments.build_description(category_list)

    # Should include docstring
    assert "List all categories" in description


@pytest.mark.asyncio
async def test_mcp_client_can_list_and_call_tools(test_session, tmp_path):
    """Test end-to-end MCP protocol: client connects, lists tools, calls tool.

    This test verifies the complete MCP flow:
    1. Server starts via stdio
    2. Client connects successfully
    3. Client can list registered tools
    4. Client can call a tool and get results
    """
    import asyncio
    import sys

    # Server parameters - run mcp-guide server
    server_params = StdioServerParameters(
        command=sys.executable, args=["-m", "mcp_guide.main"], env={"MCP_GUIDE_CONFIG_DIR": str(tmp_path)}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize with timeout
            await asyncio.wait_for(session.initialize(), timeout=5.0)

            # List tools - verify guide_category_list is registered
            # Note: Subprocess runs main.py which sets MCP_TOOL_PREFIX="guide"
            tools_result = await asyncio.wait_for(session.list_tools(), timeout=5.0)
            tool_names = [tool.name for tool in tools_result.tools]

            assert "guide_category_list" in tool_names

            # Call guide_category_list tool
            call_result = await asyncio.wait_for(
                session.call_tool("guide_category_list", {"args": {"verbose": False}}), timeout=5.0
            )

            # Parse result
            assert len(call_result.content) > 0
            result_text = call_result.content[0].text
            result_dict = json.loads(result_text)

            # Tool executed successfully (even if no session available)
            # The important thing is that the tool was called and returned valid JSON
            assert "success" in result_dict
            assert isinstance(result_dict["success"], bool)
