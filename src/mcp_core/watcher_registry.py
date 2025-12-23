"""Watcher registry for managing PathWatcher instances."""
import asyncio
from typing import TYPE_CHECKING, Callable, Optional
from weakref import WeakValueDictionary

if TYPE_CHECKING:
    from .path_watcher import PathWatcher


class WatcherRegistry:
    """Registry for managing PathWatcher instances to prevent duplicates."""

    def __init__(self) -> None:
        self._watchers: WeakValueDictionary[str, "PathWatcher"] = WeakValueDictionary()
        self._lock = asyncio.Lock()

    async def register(self, path: str, watcher: "PathWatcher") -> None:
        """Register a watcher for the given path."""
        async with self._lock:
            if path in self._watchers:
                raise ValueError(f"PathWatcher already exists for path: {path}")
            self._watchers[path] = watcher

    def get(self, path: str) -> Optional["PathWatcher"]:
        """Get existing watcher for path, or None if not found."""
        return self._watchers.get(path)

    async def unregister(self, path: str) -> None:
        """Remove watcher for the given path."""
        async with self._lock:
            self._watchers.pop(path, None)

    async def get_or_create(self, path: str, factory_func: Callable[[], "PathWatcher"]) -> "PathWatcher":
        """Get existing watcher or create new one if it doesn't exist.

        Args:
            path: File or directory path
            factory_func: Function to create new PathWatcher if needed

        Returns:
            PathWatcher instance for the path
        """
        async with self._lock:
            if path in self._watchers:
                return self._watchers[path]

            watcher = factory_func()
            self._watchers[path] = watcher
            return watcher

    async def cleanup_stopped(self) -> None:
        """Remove watchers that are no longer running."""
        async with self._lock:
            stopped_paths = []
            for path, watcher in list(self._watchers.items()):
                if not watcher.is_running():
                    stopped_paths.append(path)

            for path in stopped_paths:
                self._watchers.pop(path, None)


# Global registry instance
_global_registry: Optional[WatcherRegistry] = None


def get_global_registry() -> WatcherRegistry:
    """Get the global watcher registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = WatcherRegistry()
    return _global_registry
