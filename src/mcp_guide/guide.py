"""GuideMCP - Extended FastMCP server."""

from typing import Any, Awaitable, Callable

from fastmcp import FastMCP


class GuideMCP(FastMCP):
    """Extended FastMCP with startup handler registration."""

    def __init__(self, name: str | None = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(name, *args, **kwargs)
        self._startup_handlers: list[Callable[[], Awaitable[None]]] = []

    def on_init(self) -> Callable[[Callable[[], Awaitable[None]]], Callable[[], Awaitable[None]]]:
        """Decorator to register startup initialization handlers."""

        def decorator(func: Callable[[], Awaitable[None]]) -> Callable[[], Awaitable[None]]:
            self._startup_handlers.append(func)
            return func

        return decorator
