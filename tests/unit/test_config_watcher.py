"""Tests for simplified ConfigWatcher functionality."""

import asyncio
from unittest.mock import Mock

import pytest

from mcp_guide.watchers.config_watcher import ConfigWatcher


class TestConfigWatcher:
    """Test ConfigWatcher functionality."""

    @pytest.mark.asyncio
    async def test_config_watcher_requires_existing_file(self):
        """ConfigWatcher requires config file to exist on first check."""
        non_existent_config = "/nonexistent/config.yaml"

        watcher = ConfigWatcher(non_existent_config)
        with pytest.raises(FileNotFoundError, match="Path does not exist"):
            await watcher.has_changed()

    @pytest.mark.asyncio
    async def test_config_watcher_detects_file_changes(self, tmp_path):
        """ConfigWatcher detects when config file is modified."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("initial: value")

        callback = Mock()
        watcher = ConfigWatcher(str(config_file), callback, poll_interval=0.05)

        await watcher.start()

        # Modify file
        await asyncio.sleep(0.05)
        config_file.write_text("modified: value")

        # Wait for detection (a few poll intervals)
        await asyncio.sleep(0.2)

        await watcher.stop()

        # Should detect change
        callback.assert_called_with(str(config_file))

    @pytest.mark.asyncio
    async def test_multiple_callbacks_receive_notifications(self, tmp_path):
        """Multiple callbacks can be registered and all receive notifications."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("initial: value")

        callback1 = Mock()
        callback2 = Mock()

        watcher = ConfigWatcher(str(config_file), callback1, poll_interval=0.05)
        watcher.add_callback(callback2)

        await watcher.start()

        # Modify file
        await asyncio.sleep(0.05)
        config_file.write_text("modified: value")

        # Wait for detection (a few poll intervals)
        await asyncio.sleep(0.2)

        await watcher.stop()

        # Both callbacks should be called
        callback1.assert_called_with(str(config_file))
        callback2.assert_called_with(str(config_file))

    @pytest.mark.asyncio
    async def test_callback_exceptions_dont_crash_watcher(self, tmp_path):
        """Callback exceptions don't crash the watcher."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("initial: value")

        def failing_callback(path):
            raise Exception("Callback error")

        good_callback = Mock()

        watcher = ConfigWatcher(str(config_file), failing_callback, poll_interval=0.05)
        watcher.add_callback(good_callback)

        await watcher.start()

        # Modify file
        await asyncio.sleep(0.05)
        config_file.write_text("modified: value")

        # Wait for detection (a few poll intervals)
        await asyncio.sleep(0.2)

        await watcher.stop()

        # Good callback should still be called despite failing callback
        good_callback.assert_called_with(str(config_file))

    @pytest.mark.asyncio
    async def test_watcher_lifecycle_management(self, tmp_path):
        """Watcher can be started and stopped properly."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("test: content")

        watcher = ConfigWatcher(str(config_file))

        # Should start successfully
        await watcher.start()
        assert watcher._task is not None
        assert not watcher._task.done()

        # Should stop successfully
        await watcher.stop()
        assert watcher._task is None or watcher._task.done()
