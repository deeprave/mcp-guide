"""Main entry point for mcp-guide MCP server."""

import asyncio
import os


def _configure_environment() -> None:
    """Configure environment variables before server initialization."""
    if "MCP_TOOL_PREFIX" not in os.environ:
        os.environ["MCP_TOOL_PREFIX"] = "guide"


def _configure_logging() -> None:
    """Configure logging from environment variables."""
    from mcp_core.mcp_log import configure, get_logger

    log_level = os.environ.get("MG_LOG_LEVEL", "INFO").upper()
    log_file = os.environ.get("MG_LOG_FILE", "")
    log_json = os.environ.get("MG_LOG_JSON", "").lower() in ("true", "1", "yes")

    configure(
        level=log_level,
        file_path=log_file if log_file else None,
        json_format=log_json,
    )

    logger = get_logger(__name__)
    logger.info("Starting mcp-guide server")
    logger.debug(f"Log level: {log_level}, File: {log_file or 'none'}, JSON: {log_json}")


async def async_main() -> None:
    """Async entry point - starts MCP server with STDIO transport."""
    from mcp_guide.server import create_server

    mcp = create_server()
    await mcp.run_stdio_async()


def main() -> None:
    """MCP Guide Server - Main entry point."""
    _configure_environment()
    _configure_logging()
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
