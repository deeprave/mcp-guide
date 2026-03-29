"""MCP server creation and configuration."""

import os
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Optional

if TYPE_CHECKING:
    from mcp_guide.cli import ServerConfig

from mcp_guide import __version__
from mcp_guide.context.tasks import ClientContextTask  # noqa: F401 - imported for @task_init decorator side effects
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_decorator import ExtMcpToolDecorator
from mcp_guide.guide import GuideMCP
from mcp_guide.openspec.task import OpenSpecTask  # noqa: F401 - imported for @task_init decorator side effects

# Import task managers early to trigger @task_init decorators
from mcp_guide.task_manager import TaskManager  # noqa: F401 - imported for initialization side effects
from mcp_guide.tasks.document_task import DocumentTask  # noqa: F401 - imported for @task_init decorator side effects
from mcp_guide.tasks.retry_task import RetryTask  # noqa: F401 - imported for @task_init decorator side effects
from mcp_guide.tasks.update_task import McpUpdateTask  # noqa: F401 - imported for @task_init decorator side effects
from mcp_guide.workflow.tasks import WorkflowMonitorTask  # noqa: F401 - imported for @task_init decorator side effects

logger = get_logger(__name__)

# Holds the MiddlewareServerSession for the current notification dispatch task.
# Set by the patched _handle_message; read by _handle_roots_changed.
_current_notification_session: ContextVar[Optional[Any]] = ContextVar("_current_notification_session", default=None)


async def _handle_roots_changed(_notification: Any) -> None:
    """Handle roots/list_changed notification: bind or switch project if roots changed."""
    from mcp_guide.session import get_session_by_mcp_session

    mcp_session = _current_notification_session.get()
    if mcp_session is None:
        return

    session = get_session_by_mcp_session(mcp_session)
    if session is None:
        logger.debug(
            "roots/list_changed received before session exists; roots will be picked up on next session creation"
        )
        return

    try:
        roots_result = await mcp_session.list_roots()
        new_roots = list(roots_result.roots or [])
    except Exception as e:
        logger.debug("Failed to list roots in roots_changed handler: %s", e)
        return

    if new_roots == session.roots:
        return

    await session.try_bind_from_roots(new_roots)
    session.template_cache.invalidate()


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
            logger.error(f"Startup handler {handler.__name__} failed: {e}", exc_info=True)  # ty: ignore[unresolved-attribute]

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
        return self._instance.resource(*args, **kwargs)


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
    logger.info(f"Starting mcp-guide server; version {__version__}")
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

    # Patch _handle_message to capture the MiddlewareServerSession in a ContextVar
    # so that notification handlers can look up the per-client guide Session.
    # Guard: skip if already patched (sentinel) or required attributes are absent.
    from mcp import types as mcp_types

    low_level = mcp._mcp_server
    if not hasattr(low_level, "_handle_message") or not hasattr(low_level, "notification_handlers"):
        logger.warning("MCP server missing expected attributes; roots change handler not registered")
    elif not getattr(low_level._handle_message, "_roots_patched", False):
        import inspect

        _orig_handle_message = low_level._handle_message
        _sig = inspect.signature(_orig_handle_message)

        async def _patched_handle_message(*args: Any, **kwargs: Any) -> None:
            try:
                bound = _sig.bind_partial(*args, **kwargs)
                message = bound.arguments.get("message")
                session = bound.arguments.get("session")
            except TypeError:
                return await _orig_handle_message(*args, **kwargs)
            if isinstance(message, mcp_types.ClientNotification) and session is not None:
                token = _current_notification_session.set(session)
                try:
                    return await _orig_handle_message(*args, **kwargs)
                finally:
                    _current_notification_session.reset(token)
            return await _orig_handle_message(*args, **kwargs)

        _patched_handle_message._roots_patched = True  # ty: ignore[unresolved-attribute]
        low_level._handle_message = _patched_handle_message  # ty: ignore[invalid-assignment]

        from mcp.types import RootsListChangedNotification

        low_level.notification_handlers[RootsListChangedNotification] = _handle_roots_changed

    return mcp
