"""Integration tests for tool registration with FastMCP.

Tests that tools are correctly registered and discoverable through MCP protocol.
"""

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


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

            assert init_result.server_info.name == "guide"
            assert init_result.capabilities.tools is not None

            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            assert "get_project" in tool_names


@pytest.mark.anyio
async def test_unverified_stdio_requires_explicit_binding_despite_pwd_opt_in(tmp_path):
    """An unverified subprocess cannot infer the client root from server PWD."""
    import sys

    from fastmcp import Client
    from fastmcp.client import StdioTransport

    project_root = tmp_path / "project"
    project_root.mkdir()
    config_dir = tmp_path / "config"
    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "mcp_guide.main", "--configdir", str(config_dir)],
        env={
            "MCP_GUIDE_DISABLE_SERVER_TASKS": "1",
            "PWD": str(project_root),
            "MG_USE_PWD": "1",
        },
        cwd=str(project_root),
    )

    async with Client(transport, mode="2026-07-28") as client:
        unbound = await client.call_tool("get_project", {"args": {}}, raise_on_error=False)
        assert unbound.is_error
        result = await client.call_tool("set_project", {"args": {"path": str(project_root)}})

    assert result.structured_content is not None
    payload = result.structured_content
    assert payload["success"] is True
    assert payload["value"]["project"] == "project"
    assert isinstance(payload["session_id"], str)
    assert payload["session_id"]
