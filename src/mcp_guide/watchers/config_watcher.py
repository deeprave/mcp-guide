"""Configuration file watcher that extends PathWatcher."""

import os
from typing import Callable, Optional

from mcp_core.path_watcher import PathWatcher


class ConfigWatcher(PathWatcher):
    """Configuration-specific watcher that extends PathWatcher with config features."""

    def __init__(self, config_path: str, callback: Optional[Callable[[str], None]] = None, poll_interval: float = 1.0):
        """Initialize ConfigWatcher.

        Args:
            config_path: Path to configuration file (must exist)
            callback: Optional callback for change notifications
            poll_interval: Polling interval in seconds
        """
        # Initialize caching (path is stored in parent class as self.path)
        self._cached_content: Optional[str] = None
        self._cache_valid = False

        super().__init__(config_path, callback, poll_interval)

    @property
    def config_path(self) -> str:
        """Get the configuration file path."""
        return self.path

    def get_cached_content(self) -> Optional[str]:
        """Get cached file content.

        Returns:
            File content or None if file doesn't exist or read error
        """
        if not self._cache_valid or self._cached_content is None:
            self._load_content()

        return self._cached_content

    def invalidate_cache(self) -> None:
        """Invalidate the content cache."""
        self._cache_valid = False
        self._cached_content = None

    def _load_content(self) -> None:
        """Load and cache content from file."""
        if not os.path.exists(self.config_path):
            self._cached_content = None
            self._cache_valid = True
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._cached_content = f.read()
            self._cache_valid = True
        except (IOError, OSError):
            # Handle file access errors
            self._cached_content = None
            self._cache_valid = True

    def _invoke_callbacks(self) -> None:
        """Invoke all registered callbacks with config file path."""
        # Invalidate cache on any change
        self.invalidate_cache()

        # Call parent implementation
        super()._invoke_callbacks()
