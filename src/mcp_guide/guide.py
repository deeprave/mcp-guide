"""GuideMCP - Extended FastMCP server with agent info caching."""

from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional

from mcp.server import FastMCP

if TYPE_CHECKING:
    from mcp_guide.agent_detection import AgentInfo


class GuideMCP(FastMCP):
    """Extended FastMCP with agent info caching.

    Adds agent_info attribute to cache client/agent information
    across tool calls within a session.
    """

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(name, *args, **kwargs)
        self.agent_info: Optional["AgentInfo"] = None
        self._startup_handlers: list[Callable[[], Awaitable[None]]] = []

    def set_instructions(self, instructions: str) -> None:
        """Set server instructions sent to client during initialization.

        Args:
            instructions: Instructions text to send to the agent
        """
        self._mcp_server.instructions = instructions

    def on_init(self) -> Callable[[Callable[[], Awaitable[None]]], Callable[[], Awaitable[None]]]:
        """Decorator to register startup initialization handlers.

        Handlers are executed during server startup before any client connections.

        Example:
            @guide.on_init()
            async def initialize_something():
                # Initialization code here
                pass

        Returns:
            Decorator function that registers the handler
        """

        def decorator(func: Callable[[], Awaitable[None]]) -> Callable[[], Awaitable[None]]:
            self._startup_handlers.append(func)
            return func

        return decorator
