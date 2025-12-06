"""MCP server creation and configuration."""

import os
from typing import Any, Callable, Optional

from mcp.server import FastMCP

from mcp_core.tool_decorator import ExtMcpToolDecorator


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


def create_server() -> FastMCP:
    """Create and configure the MCP Guide server.

    Returns:
        Configured FastMCP instance
    """
    from mcp_core.mcp_log import restore_logging_config

    mcp = FastMCP(
        name="mcp-guide",
        instructions="MCP server for project documentation and development guidance",
    )

    # Restore our logging configuration after FastMCP init
    restore_logging_config()

    # Create tool decorator and set proxy instance
    decorator = ExtMcpToolDecorator(mcp)
    tools.set_instance(decorator)

    # Import tool modules - decorators register immediately
    from mcp_guide.tools import tool_category, tool_collection, tool_content  # noqa: F401

    if os.environ.get("MCP_INCLUDE_EXAMPLE_TOOLS", "").lower() in ("true", "1", "yes"):
        from mcp_guide.tools import tool_example  # noqa: F401

    return mcp
