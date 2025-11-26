"""Main entry point for mcp-guide MCP server."""

import asyncio


async def async_main() -> None:
    """Async entry point - starts MCP server with STDIO transport."""
    from mcp_guide.server import create_server

    mcp = create_server()
    await mcp.run_stdio_async()


def main() -> None:
    """MCP Guide Server - Main entry point."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
