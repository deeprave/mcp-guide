"""MCP server creation and configuration."""

import os
from typing import Any, Callable, Optional

from mcp_core.tool_decorator import ExtMcpToolDecorator
from mcp_guide.guide import GuideMCP


class _ToolsProxy:
    """Proxy that defers to actual decorator when available."""

    _instance: Optional[ExtMcpToolDecorator] = None

    @classmethod
    def set_instance(cls, instance: ExtMcpToolDecorator) -> None:
        """Set the actual decorator instance.

        Args:
            instance: ExtMcpToolDecorator instance to delegate to
        """
        cls._instance = instance

    def tool(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorate a tool function.

        If instance is set, delegates to actual decorator.
        Otherwise returns no-op decorator.

        Args:
            *args: Positional arguments for decorator
            **kwargs: Keyword arguments for decorator

        Returns:
            Decorator function
        """
        if self._instance is None:
            # Before server init - return no-op decorator
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                return func

            return decorator
        return self._instance.tool(*args, **kwargs)


# Module-level instance for imports
tools = _ToolsProxy()

# Pending log config set by main.py before server creation
_pending_log_config: Any = None


def _configure_logging_after_fastmcp() -> None:
    """Configure logging after FastMCP initialization.

    FastMCP reconfigures logging during init, so we apply our config after.
    """
    import logging

    from mcp_core.mcp_log import (
        add_trace_to_context,
        create_console_handler,
        create_file_handler,
        create_formatter,
        get_log_level,
        initialize_trace_level,
        register_cleanup_handlers,
    )

    # Always initialize TRACE level and context
    initialize_trace_level()
    add_trace_to_context()

    if _pending_log_config is None:
        return

    config = _pending_log_config

    # Get desired log level
    log_level = get_log_level(config.log_level)

    # Adjust FastMCP loggers if they're more verbose than our level
    root = logging.getLogger()
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(logger_name)
        if logger.level < log_level:
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

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Starting mcp-guide server")
    logger.debug(f"Log level: {config.log_level}, File: {config.log_file or 'none'}, JSON: {config.log_json}")


def create_server() -> GuideMCP:
    """Create and configure the MCP Guide server.

    Returns:
        Configured GuideMCP instance
    """
    mcp = GuideMCP(
        name="mcp-guide",
        instructions="MCP server for project documentation and development guidance",
    )

    # Configure logging after FastMCP init
    _configure_logging_after_fastmcp()

    # Create tool decorator and set proxy instance
    decorator = ExtMcpToolDecorator(mcp)
    tools.set_instance(decorator)

    # Import tool modules - decorators register immediately
    from mcp_guide.tools import (  # noqa: F401
        tool_category,
        tool_collection,
        tool_content,
        tool_project,
        tool_utility,
    )

    if os.environ.get("MCP_INCLUDE_EXAMPLE_TOOLS", "").lower() in ("true", "1", "yes"):
        from mcp_guide.tools import tool_example  # noqa: F401

    return mcp
