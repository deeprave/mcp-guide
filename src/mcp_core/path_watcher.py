"""Generic path watcher for monitoring file and directory changes."""

import asyncio
import logging
from pathlib import Path
from typing import Callable, List, Optional, Union

from anyio import Path as AsyncPath

logger = logging.getLogger(__name__)


class PathWatcher:
    """Generic watcher for monitoring file or directory changes."""

    def __init__(
        self, path: Union[str, Path], callback: Optional[Callable[[str], None]] = None, poll_interval: float = 1.0
    ):
        """Initialize PathWatcher with a file or directory path.

        Args:
            path: File or directory path to monitor
            callback: Optional callback function to invoke on changes
            poll_interval: Polling interval in seconds (default: 1.0)

        Raises:
            FileNotFoundError: If the path does not exist (checked on first start)
        """
        self.path = str(path)
        self.poll_interval = poll_interval

        # Initialize callback system
        self._callbacks: List[Callable[[str], None]] = []
        if callback:
            self._callbacks.append(callback)

        # Initialize async task management
        self._task: Optional[asyncio.Task[None]] = None
        self._start_lock = asyncio.Lock()

        # Track file stats for change detection (initialized on first start)
        self._last_mtime: Optional[float] = None
        self._last_inode: Optional[int] = None
        self._initialized = False

    def add_callback(self, callback: Callable[[str], None]) -> None:
        """Add a callback to be invoked when changes are detected."""
        self._callbacks.append(callback)

    def _invoke_callbacks(self) -> None:
        """Invoke all registered callbacks with path."""
        for callback in self._callbacks:
            try:
                callback(self.path)
            except Exception as e:
                # Callback exceptions should not crash the watcher
                logger.exception(f"Error in callback for path {self.path}: {e}")

    async def has_changed(self) -> bool:
        """Check if the path has changed since last check."""
        async_path = AsyncPath(self.path)

        # Initialize on first call
        if not self._initialized:
            if not await async_path.exists():
                raise FileNotFoundError(f"Path does not exist: {self.path}")

            try:
                stat = await async_path.stat()
                self._last_mtime = stat.st_mtime
                self._last_inode = stat.st_ino
                self._initialized = True
                return False
            except (OSError, FileNotFoundError) as e:
                raise FileNotFoundError(f"Path does not exist: {self.path}") from e

        # Check if path still exists
        try:
            if not await async_path.exists():
                # File was deleted - trigger callback
                self._invoke_callbacks()
                return True

            stat = await async_path.stat()
            current_mtime = stat.st_mtime
            current_inode = stat.st_ino

            # Check for changes
            mtime_changed = current_mtime != self._last_mtime
            inode_changed = current_inode != self._last_inode

            if mtime_changed or inode_changed:
                # Update tracked values
                self._last_mtime = current_mtime
                self._last_inode = current_inode

                # Invoke callbacks
                self._invoke_callbacks()

                return True

            return False
        except (OSError, FileNotFoundError):
            # File was deleted or became inaccessible after initialization
            self._invoke_callbacks()
            return True

    async def start(self) -> None:
        """Start monitoring the path for changes.

        Creates and starts an asyncio task that polls for changes.
        Multiple calls to start() will not create duplicate tasks.
        """
        async with self._start_lock:
            if self.is_running():
                return  # Already running, don't create duplicate task

            self._task = asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        """Stop monitoring and clean up resources."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        return self._task is not None and not self._task.done()

    async def _monitor_loop(self) -> None:
        """Internal monitoring loop that polls for changes."""
        while True:
            try:
                await self.has_changed()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                # Handle other exceptions gracefully - keep running after logging
                logger.exception(f"Error in monitor loop for {self.path}: {e}")
                await asyncio.sleep(self.poll_interval)
