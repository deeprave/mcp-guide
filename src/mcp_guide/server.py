"""MCP server creation and configuration."""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from fastmcp import FastMCP

if TYPE_CHECKING:
    from mcp_guide.cli import ServerConfig
    from mcp_guide.session import Session

from mcp_guide import __version__
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.runtime import GuideRuntime, create_runtime

logger = get_logger(__name__)


@dataclass(frozen=True)
class GuideApplication:
    """Unstarted FastMCP surface paired with its Guide application runtime."""

    server: FastMCP
    runtime: GuideRuntime["Session"]


def _initialize_runtime_tasks() -> None:
    """Import runtime task modules so task decorators run.

    Tests that only need MCP bootstrap can disable this at server startup
    without changing global decorator semantics.
    """
    if os.environ.get("MCP_GUIDE_DISABLE_SERVER_TASKS", "").lower() in ("1", "true", "yes"):
        return

    from mcp_guide.context.tasks import ClientContextTask  # noqa: F401
    from mcp_guide.openspec.task import OpenSpecTask  # noqa: F401
    from mcp_guide.task_manager import TaskManager  # noqa: F401
    from mcp_guide.tasks.document_task import DocumentTask  # noqa: F401
    from mcp_guide.tasks.retry_task import RetryTask  # noqa: F401
    from mcp_guide.tasks.update_task import McpUpdateTask  # noqa: F401
    from mcp_guide.workflow.tasks import WorkflowMonitorTask  # noqa: F401


# Export mcp instance for direct import
mcp: Optional[FastMCP] = None


def _configure_logging_after_fastmcp(config: "ServerConfig") -> None:
    """Configure logging after FastMCP initialization.

    FastMCP reconfigures logging during init, so we apply our config after.

    Args:
        config: Server configuration with logging settings
    """
    import logging

    from mcp_guide.core.mcp_log import (
        add_trace_to_context,
        create_console_handler,
        create_file_handler,
        create_formatter,
        get_log_level,
        register_cleanup_handlers,
    )

    # Always add trace to context
    add_trace_to_context()

    # Get desired log level
    log_level = get_log_level(config.log_level)

    # Get root logger
    root = logging.getLogger()

    # Adjust FastMCP loggers if they're more verbose than our level.
    # Use getEffectiveLevel() so we don't override loggers that inherit
    # an appropriate level from their parents (i.e. those with level=NOTSET).
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(logger_name)
        # Skip non-Logger placeholders in loggerDict
        if not isinstance(logger, logging.Logger):
            continue
        if logger.getEffectiveLevel() < log_level:
            logger.setLevel(log_level)

    # Create our handlers
    console_handler = create_console_handler()
    file_handler = create_file_handler(config.log_file) if config.log_file else None

    # Apply formatters
    formatter = create_formatter(config.log_json)
    console_handler.setFormatter(formatter)
    if file_handler:
        file_handler.setFormatter(formatter)

    # Configure root logger with our handlers and level
    root.setLevel(log_level)
    console_handler.setLevel(log_level)
    root.addHandler(console_handler)
    if file_handler:
        file_handler.setLevel(log_level)
        root.addHandler(file_handler)

    # Configure mcp_guide loggers to not propagate and use root handlers
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        if logger_name.startswith("mcp_guide") or logger_name.startswith("fastmcp.mcp_guide"):
            logger = logging.getLogger(logger_name)
            logger.propagate = False
            logger.setLevel(log_level)
            for handler in root.handlers:
                if handler not in logger.handlers:
                    logger.addHandler(handler)

    # Register cleanup handlers
    register_cleanup_handlers()

    # Replay any log records emitted before handlers were attached
    from mcp_guide.core.mcp_log import flush_startup_buffer

    flush_startup_buffer()

    # Log startup message
    logger.info(f"Starting mcp-guide server; version {__version__}")
    logger.debug(f"Log level: {config.log_level}, File: {config.log_file or 'none'}, JSON: {config.log_json}")


def create_application(config: "ServerConfig") -> GuideApplication:
    """Construct the unstarted FastMCP surface and Guide runtime.

    Args:
        config: Server configuration

    Returns:
        Unstarted FastMCP surface and its explicit runtime lifecycle
    """
    global mcp

    async def start_runtime() -> None:
        """Apply process-level Guide configuration before serving begins."""
        if config.configdir:
            from mcp_guide.config_paths import set_config_dir

            set_config_dir(config.configdir)
        if config.docroot:
            from mcp_guide.config_paths import set_docroot

            set_docroot(config.docroot)

        _configure_logging_after_fastmcp(config)
        _initialize_runtime_tasks()

    from mcp_guide.session import Session

    runtime: GuideRuntime[Session]

    def create_session(_owner: object) -> Session:
        return Session(runtime)

    runtime = create_runtime(
        create_session,
        config_dir=config.configdir,
        docroot=config.docroot,
        on_start=start_runtime,
    )

    # Use MCP_GUIDE_NAME env var if set, otherwise use generic name
    server_name = os.getenv("MCP_GUIDE_NAME", "guide")
    mcp = FastMCP(
        name=server_name,
        instructions="MCP server for project documentation and development guidance",
        lifespan=lambda _server: runtime.lifespan(),
    )

    # Set tool prefix from config
    os.environ["MCP_TOOL_PREFIX"] = config.tool_prefix

    # Register tools with MCP
    from mcp_guide.core.tool_decorator import register_tools

    register_tools(mcp)

    # Import prompt and resource modules
    from mcp_guide import resources as resource_module  # noqa: F401

    # Register prompts and resources with MCP
    from mcp_guide.core.prompt_decorator import register_prompts
    from mcp_guide.core.resource_decorator import register_resources
    from mcp_guide.prompts import guide_prompt  # noqa: F401

    register_prompts(mcp)
    register_resources(mcp)

    return GuideApplication(server=mcp, runtime=runtime)


def create_server(config: "ServerConfig") -> FastMCP:
    """Construct the unstarted FastMCP surface for compatibility callers."""
    return create_application(config).server
