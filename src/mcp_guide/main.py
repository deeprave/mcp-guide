"""Main entry point for mcp-guide MCP server."""

import asyncio
import logging
import os
import sys

import click

from mcp_guide.cli import ServerConfig, parse_args
from mcp_guide.config import DocrootError


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
    from mcp_core.mcp_log import (
        add_trace_to_context,
        create_console_handler,
        create_file_handler,
        create_formatter,
        get_log_level,
        initialize_trace_level,
        register_cleanup_handlers,
        save_logging_config,
    )

    # Initialize TRACE level and context
    initialize_trace_level()
    add_trace_to_context()

    # Create handlers
    console_handler = create_console_handler()
    file_handler = create_file_handler(config.log_file) if config.log_file else None

    # Create and apply formatters
    formatter = create_formatter(config.log_json)
    console_handler.setFormatter(formatter)
    if file_handler:
        file_handler.setFormatter(formatter)

    # Configure root logger
    root = logging.getLogger()
    log_level = get_log_level(config.log_level)
    root.setLevel(log_level)
    console_handler.setLevel(log_level)
    root.addHandler(console_handler)
    if file_handler:
        file_handler.setLevel(log_level)
        root.addHandler(file_handler)

    # Save configuration for restoration after FastMCP init
    save_logging_config(console_handler, file_handler)

    # Register cleanup handlers for graceful shutdown
    register_cleanup_handlers()

    logger = logging.getLogger(__name__)
    logger.info("Starting mcp-guide server")
    logger.debug(f"Log level: {config.log_level}, File: {config.log_file or 'none'}, JSON: {config.log_json}")


def _handle_cli_error(config: ServerConfig) -> None:
    """Handle CLI errors after logging is configured.

    Args:
        config: Server configuration with potential CLI error
    """
    if not config.cli_error:
        return

    logger = logging.getLogger(__name__)

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
    config = parse_args()

    # Exit immediately for help/version (before logging setup)
    if config.should_exit and not config.cli_error:
        sys.exit(0)

    _configure_environment(config)
    _configure_logging(config)
    _handle_cli_error(config)

    try:
        asyncio.run(async_main())
    except DocrootError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"FATAL: {e}")
        logger.error("MCP server cannot function without a valid docroot. Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
