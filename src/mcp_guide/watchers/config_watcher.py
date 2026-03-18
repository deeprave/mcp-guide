"""Configuration file watcher that extends PathWatcher with config features."""

from typing import Optional

from mcp_guide.core.path_watcher import PathWatcher, WatcherCallback


class ConfigWatcher(PathWatcher):
    """Configuration file watcher with lazy path validation."""

    def __init__(self, config_path: str, callback: Optional[WatcherCallback] = None, poll_interval: float = 1.0):
        """Initialize ConfigWatcher.

        Args:
            config_path: Path to configuration file (validated when monitoring starts)
            callback: Optional callback for change notifications
            poll_interval: Polling interval in seconds
        """
        super().__init__(config_path, callback, poll_interval)

    @property
    def config_path(self) -> str:
        """Get the configuration file path."""
        return self.path
