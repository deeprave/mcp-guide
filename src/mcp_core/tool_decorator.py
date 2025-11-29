"""Extended MCP tool decorator with logging and prefixing."""

import inspect
import os
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Optional

from mcp_core.mcp_log import get_logger

logger = get_logger(__name__)

# Internal test mode control - not exposed to external manipulation
_test_mode: ContextVar[bool] = ContextVar("tool_test_mode", default=False)


def enable_test_mode() -> None:
    """Enable test mode (for testing only)."""
    _test_mode.set(True)


def disable_test_mode() -> None:
    """Disable test mode."""
    _test_mode.set(False)


class ExtMcpToolDecorator:
    """Extended MCP tool decorator with logging and prefix support.

    Features:
    - Reads MCP_TOOL_PREFIX from environment
    - Per-tool prefix override
    - TRACE/DEBUG/ERROR logging
    - Exception re-raising after logging
    """

    def __init__(self, mcp: Any):
        """Initialize decorator.

        Args:
            mcp: FastMCP instance
        """
        self.mcp = mcp

    def tool(
        self,
        args_class: Optional[type] = None,
        description: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorate a tool function with logging and prefixing.

        Args:
            args_class: ToolArguments subclass (auto-generates description)
            description: Tool description (overrides auto-generation)
            prefix: Tool name prefix (overrides MCP_TOOL_PREFIX)

        Returns:
            Decorator function
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            # In test mode, return function unchanged
            if _test_mode.get():
                return func

            # Auto-generate description from args_class if provided
            final_description = description
            if args_class is not None and description is None:
                from mcp_core.tool_arguments import ToolArguments

                final_description = ToolArguments.build_tool_description(func)

            # Determine prefix
            tool_prefix = prefix if prefix is not None else os.environ.get("MCP_TOOL_PREFIX", "")

            # Build tool name
            tool_name = f"{tool_prefix}_{func.__name__}" if tool_prefix else func.__name__

            # Wrap function with logging
            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    logger.trace(f"Invoking async tool: {tool_name}")  # type: ignore[attr-defined]
                    try:
                        result = await func(*args, **kwargs)
                        logger.debug(f"Tool {tool_name} completed successfully")
                        return result
                    except Exception as e:
                        logger.error(f"Tool {tool_name} failed: {e}")
                        raise

                wrapped = async_wrapper
            else:

                @wraps(func)
                def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                    logger.trace(f"Invoking sync tool: {tool_name}")  # type: ignore[attr-defined]
                    try:
                        result = func(*args, **kwargs)
                        logger.debug(f"Tool {tool_name} completed successfully")
                        return result
                    except Exception as e:
                        logger.error(f"Tool {tool_name} failed: {e}")
                        raise

                wrapped = sync_wrapper

            # Register with FastMCP
            self.mcp.tool(name=tool_name, description=final_description)(wrapped)

            return wrapped

        return decorator
