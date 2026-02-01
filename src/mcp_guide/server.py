"""MCP server creation and configuration."""

import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Optional

if TYPE_CHECKING:
    from mcp_guide.cli import ServerConfig

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

from mcp_guide.context.tasks import ClientContextTask  # noqa: F401 - imported for @task_init decorator side effects
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_decorator import ExtMcpToolDecorator
from mcp_guide.guide import GuideMCP
from mcp_guide.openspec.task import OpenSpecTask  # noqa: F401 - imported for @task_init decorator side effects

# Import task managers early to trigger @task_init decorators
from mcp_guide.task_manager import TaskManager  # noqa: F401 - imported for initialization side effects
from mcp_guide.workflow.tasks import WorkflowMonitorTask  # noqa: F401 - imported for @task_init decorator side effects

logger = get_logger(__name__)


@asynccontextmanager
async def guide_lifespan(server: GuideMCP) -> AsyncIterator[dict[str, Any]]:
    """Lifespan hook for server initialization and shutdown.

    Executes all registered startup handlers during server startup,
    before any client connections are accepted.

    Args:
        server: The GuideMCP server instance

    Yields:
        Empty dict (required by FastMCP lifespan protocol)
    """
    # Startup: Execute all registered handlers
    for handler in server._startup_handlers:
        try:
            await handler()
        except Exception as e:
            logger.error(f"Startup handler {handler.__name__} failed: {e}", exc_info=True)

    yield {}  # Server runs

    # Shutdown: cleanup if needed (future)


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


class _ResourcesProxy:
    """Proxy that defers to actual resource decorator when available."""

    _instance: Optional[Any] = None

    @classmethod
    def set_instance(cls, instance: Any) -> None:
        """Set the actual server instance.

        Args:
            instance: FastMCP server instance to delegate to
        """
        cls._instance = instance

    def resource(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorate a resource function.

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
        return self._instance.resource(*args, **kwargs)  # type: ignore[no-any-return]


# Module-level instances for imports
tools = _ToolsProxy()
resources = _ResourcesProxy()

# Export mcp instance for direct import
mcp: Optional[GuideMCP] = None


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

    # Log startup message
    logger.info("Starting mcp-guide server")
    logger.debug(f"Log level: {config.log_level}, File: {config.log_file or 'none'}, JSON: {config.log_json}")


def create_server(config: "ServerConfig") -> GuideMCP:
    """Create and configure the MCP Guide server.

    Args:
        config: Server configuration

    Returns:
        Configured GuideMCP instance
    """
    global mcp

    # Set config overrides if provided from CLI
    if config.configdir:
        from mcp_guide.config_paths import set_config_dir

        set_config_dir(config.configdir)

    if config.docroot:
        from mcp_guide.config_paths import set_docroot

        set_docroot(config.docroot)

    # Use MCP_GUIDE_NAME env var if set, otherwise use generic name
    server_name = os.getenv("MCP_GUIDE_NAME", "guide")
    mcp = GuideMCP(
        name=server_name,
        instructions="MCP server for project documentation and development guidance",
        lifespan=guide_lifespan,
    )

    # Configure logging after FastMCP init
    _configure_logging_after_fastmcp(config)

    # Set tool prefix from config
    os.environ["MCP_TOOL_PREFIX"] = config.tool_prefix

    # Task managers are automatically instantiated and registered via @task_init decorators

    # Create tool decorator and set proxy instance
    tool_decorator = ExtMcpToolDecorator(mcp)
    tools.set_instance(tool_decorator)
    resources.set_instance(mcp)

    # Register task manager initialization
    @mcp.on_init()
    async def initialize_task_manager() -> None:
        """Initialize task manager and all registered tasks."""
        from mcp_guide.task_manager.manager import get_task_manager

        task_manager = get_task_manager()
        await task_manager.on_init()

    # Import tool modules - decorators register immediately
    from mcp_guide.tools import (  # noqa: F401
        tool_category,
        tool_collection,
        tool_content,
        tool_feature_flags,
        tool_filesystem,
        tool_project,
        tool_utility,
    )

    if os.environ.get("MCP_INCLUDE_EXAMPLE_TOOLS", "").lower() in ("true", "1", "yes"):
        from mcp_guide.tools import tool_example  # noqa: F401

    # Import prompt modules - decorators register immediately
    # Import resource modules - decorators register immediately
    from mcp_guide import resources as resource_module  # noqa: F401
    from mcp_guide.prompts import guide_prompt  # noqa: F401

    return mcp
