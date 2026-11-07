"""Integration tests for tool registration with FastMCP.

Tests that tools are correctly registered and discoverable through MCP protocol.
"""

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.anyio
@pytest.mark.slow
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


@pytest.fixture
def stdio_transport():
    """Report the stdio transport to the server, as FastMCP does when it runs over stdio.

    An in-memory client never sets FastMCP's transport context variable, and the inherited-PWD
    bind only applies to stdio, so the test states the transport it is standing in for.
    """
    from fastmcp.server.context import _current_transport

    token = _current_transport.set("stdio")
    try:
        yield
    finally:
        _current_transport.reset(token)


def _opt_in(monkeypatch, how):
    """Opt in to inherited-PWD binding through the environment variable or the --use-pwd configuration."""
    # setenv first so the variable is restored even when create_application() sets it for the flag.
    monkeypatch.setenv("MG_USE_PWD", "1" if how == "env" else "0")
    return how == "flag"


def _application(tmp_path, *, use_pwd):
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    config = ServerConfig(configdir=str(config_dir), transport_mode="stdio", use_pwd=use_pwd)
    return create_application(config)


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["2026-07-28", "legacy"])
@pytest.mark.parametrize("how", ["env", "flag"])
@pytest.mark.slow
async def test_opted_in_stdio_binds_from_pwd_that_is_the_server_directory(
    tmp_path, monkeypatch, stdio_transport, mode, how
):
    """PWD that is the server's own directory binds the first request without set_project."""
    from fastmcp import Client

    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.chdir(project_root)
    monkeypatch.setenv("PWD", str(project_root))
    application = _application(tmp_path, use_pwd=_opt_in(monkeypatch, how))

    async with Client(application.server, mode=mode) as client:
        bound = await client.call_tool("get_project", {"args": {}}, raise_on_error=False)
        session_id = bound.structured_content.get("session_id") if bound.structured_content else None
        later_args = {"args": {"session_id": session_id}} if session_id else {"args": {}}
        later = await client.call_tool("get_project", later_args, raise_on_error=False)

    assert not bound.is_error
    assert bound.structured_content is not None
    assert bound.structured_content["success"] is True
    assert bound.structured_content["value"]["project"] == "project"
    assert not later.is_error
    assert later.structured_content is not None
    assert later.structured_content["value"]["project"] == "project"


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["2026-07-28", "legacy"])
@pytest.mark.parametrize("how", ["env", "flag"])
@pytest.mark.slow
async def test_opted_in_stdio_ignores_pwd_that_is_not_the_server_directory(
    tmp_path, monkeypatch, stdio_transport, mode, how
):
    """A PWD that differs from the server's directory is not evidence, so binding stays explicit."""
    from fastmcp import Client

    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    project_root = tmp_path / "project"
    project_root.mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(project_root)
    monkeypatch.setenv("PWD", str(elsewhere))
    application = _application(tmp_path, use_pwd=_opt_in(monkeypatch, how))

    async with Client(application.server, mode=mode) as client:
        unbound = await client.call_tool("get_project", {"args": {}}, raise_on_error=False)
        assert unbound.is_error
        result = await client.call_tool("set_project", {"args": {"path": str(project_root)}})

    assert result.structured_content is not None
    payload = result.structured_content
    assert payload["success"] is True
    assert payload["value"]["project"] == "project"
    assert isinstance(payload["session_id"], str)
