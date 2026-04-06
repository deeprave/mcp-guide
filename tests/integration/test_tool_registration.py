"""Integration tests for tool registration with FastMCP.

Tests that tools are correctly registered and discoverable through MCP protocol.
"""

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_guide.core.tool_decorator import disable_test_mode, enable_test_mode


@pytest.fixture(scope="session", autouse=True)
def production_mode():
    """Ensure production mode for integration tests."""
    disable_test_mode()
    yield
    enable_test_mode()  # Restore test mode for other tests


@pytest.mark.anyio
async def test_tool_registration_with_fastmcp():
    """Test that tools register correctly with FastMCP instance."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_server

    # Create server
    config = ServerConfig()
    server = create_server(config)

    # Verify server was created
    assert server is not None
    assert server.name == "guide"

    # FastMCP should have tools registered
    # Note: FastMCP doesn't expose a direct way to list tools,
    # but we can verify the server was created successfully
    assert hasattr(server, "tool")


@pytest.mark.anyio
async def test_auto_generated_description():
    """Test that tool descriptions are auto-generated from args class."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_server

    # Create server (triggers registration)
    config = ServerConfig()
    server = create_server(config)

    # Verify description generation works
    from mcp_guide.core.tool_arguments import ToolArguments
    from mcp_guide.tools.tool_category import internal_category_list

    description = ToolArguments.build_description(internal_category_list)

    # Should include docstring
    assert "List all categories" in description


@pytest.mark.anyio
async def test_mcp_client_can_initialize_and_list_tools(tmp_path):
    """Test end-to-end stdio MCP protocol: client initializes and lists tools.

    This test verifies the complete MCP flow:
    1. Server starts via stdio
    2. Client connects successfully
    3. Client can list registered tools
    """
    import sys

    # Server parameters - run mcp-guide server.
    # This test only verifies stdio initialization and tool listing, so it
    # doesn't need an installed template set or installer config file.
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_guide.main", "--configdir", str(config_dir)],
        env={
            "MCP_GUIDE_CONFIG_DIR": str(tmp_path),
            "MCP_GUIDE_DISABLE_SERVER_TASKS": "1",
            "PWD": str(tmp_path),
        },
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            init_result = await session.initialize()

            assert init_result.serverInfo.name == "guide"
            assert init_result.capabilities.tools is not None

            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            assert "get_project" in tool_names
