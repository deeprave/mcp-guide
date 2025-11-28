"""MCP server creation and configuration."""

import os

from mcp.server import FastMCP

from mcp_core.tool_arguments import ToolArguments
from mcp_core.tool_decorator import ExtMcpToolDecorator


def create_server() -> FastMCP:
    """Create and configure the MCP Guide server.

    Returns:
        Configured FastMCP instance
    """
    mcp = FastMCP(
        name="mcp-guide",
        instructions="MCP server for project documentation and development guidance",
    )

    # Create tool decorator
    tools = ExtMcpToolDecorator(mcp)

    # Import tool modules (triggers @ToolArguments.declare)
    # Conditional example tool import
    if os.environ.get("MCP_INCLUDE_EXAMPLE_TOOLS", "").lower() in ("true", "1", "yes"):
        from mcp_guide.tools import tool_example  # noqa: F401

    # Get collected tools and register them
    declared_tools = ToolArguments.get_declared_tools()
    for name, func in declared_tools.items():
        description = ToolArguments.build_tool_description(func)
        tools.tool(description=description)(func)

    return mcp
