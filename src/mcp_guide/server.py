"""MCP server creation and configuration."""

from mcp.server import FastMCP


def create_server() -> FastMCP:
    """Create and configure the MCP Guide server.

    Returns:
        Configured FastMCP instance
    """
    mcp = FastMCP(
        name="mcp-guide",
        instructions="MCP server for project documentation and development guidance",
    )

    # Future: Register tools, prompts, and resources here

    return mcp
