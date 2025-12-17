"""Prompt decorator for FastMCP with configurable prefixes."""

import os
from typing import Any, Callable, Optional, Type

from mcp.server import FastMCP

from mcp_core.arguments import Arguments


class ExtMcpPromptDecorator:
    """Prompt decorator that adds configurable prefixes and handles Arguments classes.

    Similar to ExtMcpToolDecorator but for prompts. Reads MCP_PROMPT_PREFIX environment
    variable and defaults to empty string (no prefix).
    """

    def __init__(self, mcp: FastMCP) -> None:
        """Initialize prompt decorator.

        Args:
            mcp: FastMCP server instance
        """
        self.mcp = mcp
        self.prefix = os.environ.get("MCP_PROMPT_PREFIX", "")

    def prompt(
        self,
        args_class: Optional[Type[Arguments]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorate a prompt function for FastMCP registration.

        Args:
            args_class: Arguments subclass (auto-generates description)
            name: Override prompt name
            description: Override prompt description

        Returns:
            Decorator function
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            # Determine final name
            final_name = name or func.__name__
            if self.prefix:
                final_name = f"{self.prefix}_{final_name}"

            # Build description
            if args_class:
                final_description = args_class.build_description(func)
            else:
                final_description = description or func.__doc__ or ""

            # Register with FastMCP
            self.mcp.prompt(name=final_name, description=final_description)(func)

            return func

        return decorator
