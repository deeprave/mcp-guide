"""Main entry point for mcp-guide MCP server."""

import asyncio
import os
import sys

import click

from mcp_guide.cli import ServerConfig


def _configure_environment(config: ServerConfig) -> None:
    """Configure environment variables from config.

    Args:
        config: Server configuration
    """
    os.environ["MCP_TOOL_PREFIX"] = config.tool_prefix


def _configure_logging(config: ServerConfig) -> None:
    """Configure logging from config.

    Args:
        config: Server configuration
    """
    from mcp_core.mcp_log import configure, get_logger

    configure(
        level=config.log_level,
        file_path=config.log_file,
        json_format=config.log_json,
    )

    logger = get_logger(__name__)
    logger.info("Starting mcp-guide server")
    logger.debug(f"Log level: {config.log_level}, File: {config.log_file or 'none'}, JSON: {config.log_json}")


def _handle_cli_error(config: ServerConfig) -> None:
    """Handle CLI errors after logging is configured.

    Args:
        config: Server configuration with potential CLI error
    """
    if not config.cli_error:
        return

    from mcp_core.mcp_log import get_logger

    logger = get_logger(__name__)

    if config.should_exit:
        # Ctrl+C
        logger.info("Interrupted by user (Ctrl+C)")
        sys.exit(130)
    else:
        # Log error and continue with defaults
        error_msg = config.cli_error.format_message()
        logger.error(f"CLI error: {error_msg}")
        logger.warning("Continuing with default configuration due to CLI error")


async def async_main() -> None:
    """Async entry point - starts MCP server with STDIO transport."""
    from mcp_guide.server import create_server

    mcp = create_server()
    await mcp.run_stdio_async()


def main() -> None:
    """MCP Guide Server - Main entry point."""
    from mcp_guide.cli import parse_args

    config = parse_args()

    # Exit immediately for help/version (before logging setup)
    if config.should_exit and not config.cli_error:
        sys.exit(0)

    _configure_environment(config)
    _configure_logging(config)
    _handle_cli_error(config)
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
