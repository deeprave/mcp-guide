"""Main entry point for mcp-guide MCP server."""

import asyncio
import os
import sys

from mcp_guide.cli import ServerConfig, parse_args
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.session import DocrootError


def _setup_remote_debugging() -> None:
    """Set up remote debugging if enabled via environment variables.

    Environment variables:
        MG_DEBUG: Set to 'true' to enable remote debugging
        MG_DEBUG_PORT: Port number for debug server (default: 5678)
        MG_DEBUG_WAIT: Set to 'true' to wait for debugger to attach
    """
    if os.environ.get("MG_DEBUG", "").lower() not in ("true", "1", "yes"):
        return

    try:
        debug_port = int(os.environ.get("MG_DEBUG_PORT", "5678"))
    except ValueError:
        print(f"Warning: Invalid MG_DEBUG_PORT value '{os.environ.get('MG_DEBUG_PORT')}', using default 5678")
        debug_port = 5678
    debug_wait = os.environ.get("MG_DEBUG_WAIT", "").lower() in ("true", "1", "yes")

    # Start debug server
    import debugpy  # Optional dependency for debugging support

    debugpy.listen(("localhost", debug_port))
    print(f"Debug server listening on port {debug_port}", file=sys.stderr)

    if debug_wait:
        print("Waiting for debugger to attach...", file=sys.stderr)
        debugpy.wait_for_client()
        print("Debugger attached!", file=sys.stderr)


def _configure_environment(config: ServerConfig) -> None:
    """Configure environment variables from config.

    Args:
        config: Server configuration
    """
    os.environ["MCP_TOOL_PREFIX"] = config.tool_prefix


def _configure_logging(config: ServerConfig) -> None:
    """Store logging configuration for later initialization.

    Logging is configured AFTER FastMCP initializes to avoid conflicts.

    Args:
        config: Server configuration
    """
    # Store config globally for server.py to use after FastMCP init
    import mcp_guide.server as server_module

    server_module._pending_log_config = config


def _handle_cli_error(config: ServerConfig) -> None:
    """Handle CLI errors after logging is configured.

    Args:
        config: Server configuration with potential CLI error
    """
    if not config.cli_error:
        return

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
    config = parse_args()

    # Exit immediately for help/version (before logging setup)
    if config.should_exit and not config.cli_error:
        sys.exit(0)

    # Set up remote debugging before anything else
    _setup_remote_debugging()

    _configure_environment(config)
    _configure_logging(config)
    _handle_cli_error(config)

    try:
        asyncio.run(async_main())
    except DocrootError as e:
        logger = get_logger(__name__)
        logger.error(f"FATAL: {e}")
        logger.error("MCP server cannot function without a valid docroot. Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
