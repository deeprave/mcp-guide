"""Extended MCP tool decorator with logging and prefixing."""

import inspect
import os
from functools import wraps
from typing import Any, Callable, Optional

from mcp_core.mcp_log import get_logger

logger = get_logger(__name__)


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
        description: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorate a tool function with logging and prefixing.

        Args:
            description: Tool description
            prefix: Tool name prefix (overrides MCP_TOOL_PREFIX)

        Returns:
            Decorator function
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
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
            self.mcp.tool(name=tool_name, description=description)(wrapped)

            return wrapped

        return decorator
