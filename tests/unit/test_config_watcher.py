"""Tests for simplified ConfigWatcher functionality."""

import asyncio
from unittest.mock import Mock

import pytest

from mcp_guide.watchers.config_watcher import ConfigWatcher


class TestConfigWatcher:
    """Test ConfigWatcher functionality."""

    def test_config_watcher_requires_existing_file(self):
        """ConfigWatcher requires config file to exist at initialization."""
        non_existent_config = "/nonexistent/config.yaml"

        with pytest.raises(FileNotFoundError, match="Path does not exist"):
            ConfigWatcher(non_existent_config)

    @pytest.mark.asyncio
    async def test_config_watcher_detects_file_changes(self, tmp_path):
        """ConfigWatcher detects when config file is modified."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("initial: value")

        callback = Mock()
        watcher = ConfigWatcher(str(config_file), callback)

        await watcher.start()

        # Modify file
        await asyncio.sleep(0.1)
        config_file.write_text("modified: value")

        # Wait for detection
        await asyncio.sleep(1.2)

        await watcher.stop()

        # Should detect change
        callback.assert_called_with(str(config_file))

    def test_config_watcher_caches_file_content(self, tmp_path):
        """ConfigWatcher caches file content for efficient access."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("test: content")

        watcher = ConfigWatcher(str(config_file))

        # First access should load and cache
        content1 = watcher.get_cached_content()
        assert content1 == "test: content"

        # Second access should return cached content
        content2 = watcher.get_cached_content()
        assert content2 == "test: content"
        assert content1 is content2  # Same object reference

    def test_cache_invalidation_on_change_detection(self, tmp_path):
        """Cache is invalidated when file changes are detected."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("initial: content")

        watcher = ConfigWatcher(str(config_file))

        # Load initial content
        initial_content = watcher.get_cached_content()
        assert initial_content == "initial: content"

        # Simulate change detection by calling invalidate_cache
        watcher.invalidate_cache()

        # Modify file
        config_file.write_text("modified: content")

        # Next access should reload
        new_content = watcher.get_cached_content()
        assert new_content == "modified: content"

    def test_cache_handles_file_read_errors(self, tmp_path):
        """Cache handles file read errors gracefully."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("test: content")

        watcher = ConfigWatcher(str(config_file))

        # Delete file after watcher creation
        config_file.unlink()

        # Should handle missing file gracefully
        content = watcher.get_cached_content()
        assert content is None

    @pytest.mark.asyncio
    async def test_multiple_callbacks_receive_notifications(self, tmp_path):
        """Multiple callbacks can be registered and all receive notifications."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("initial: value")

        callback1 = Mock()
        callback2 = Mock()

        watcher = ConfigWatcher(str(config_file), callback1)
        watcher.add_callback(callback2)

        await watcher.start()

        # Modify file
        await asyncio.sleep(0.1)
        config_file.write_text("modified: value")

        # Wait for detection
        await asyncio.sleep(1.2)

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

        watcher = ConfigWatcher(str(config_file), failing_callback)
        watcher.add_callback(good_callback)

        await watcher.start()

        # Modify file
        await asyncio.sleep(0.1)
        config_file.write_text("modified: value")

        # Wait for detection
        await asyncio.sleep(1.2)

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

    @pytest.mark.asyncio
    async def test_cache_invalidated_on_file_change(self, tmp_path):
        """Cache is automatically invalidated when file changes are detected."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("initial: content")

        cache_invalidated = False

        def callback(path):
            nonlocal cache_invalidated
            cache_invalidated = True

        watcher = ConfigWatcher(str(config_file), callback)

        # Load initial content
        initial_content = watcher.get_cached_content()
        assert initial_content == "initial: content"

        await watcher.start()

        # Modify file
        await asyncio.sleep(0.1)
        config_file.write_text("modified: content")

        # Wait for detection
        await asyncio.sleep(1.2)

        await watcher.stop()

        # Cache should be invalidated and callback called
        assert cache_invalidated

        # Next access should get new content
        new_content = watcher.get_cached_content()
        assert new_content == "modified: content"
