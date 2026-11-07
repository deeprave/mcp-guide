"""Protocol-level server surface coverage."""

import pytest
from fastmcp import Client


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["legacy", "2026-07-28"])
@pytest.mark.slow
async def test_fastmcp_surface_negotiates_retained_and_modern_client_eras(mode: str) -> None:
    """The stdio runner serves FastMCP's negotiated client eras from one surface."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    application = create_application(ServerConfig())
    async with Client(application.server, mode=mode) as client:
        tools = await client.list_tools()

    tool_names = {tool.name for tool in tools}
    assert "set_project" in tool_names
    assert "switch_project" in tool_names
    assert "list_skills" in tool_names
