"""Tests for PathWatcher basic functionality."""

import asyncio
import os
import tempfile
import time
from unittest.mock import Mock

import pytest

from mcp_core.path_watcher import PathWatcher


class TestPathWatcherBasic:
    """Test basic PathWatcher instantiation and validation."""

    def test_path_watcher_can_be_instantiated_with_file_path(self):
        """PathWatcher can be instantiated with a file path."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            watcher = PathWatcher(tmp_file.name)
            assert watcher.path == tmp_file.name

    def test_path_watcher_can_be_instantiated_with_directory_path(self):
        """PathWatcher can be instantiated with a directory path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            watcher = PathWatcher(tmp_dir)
            assert watcher.path == tmp_dir

    def test_path_watcher_raises_error_for_non_existent_paths(self):
        """PathWatcher raises error for non-existent paths."""
        non_existent_path = "/this/path/does/not/exist"
        with pytest.raises(FileNotFoundError):
            PathWatcher(non_existent_path)

    def test_path_watcher_tracks_initial_mtime_and_inode(self):
        """PathWatcher tracks initial mtime and inode."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            watcher = PathWatcher(tmp_file.name)

            # Get actual file stats
            stat = os.stat(tmp_file.name)

            assert watcher._last_mtime == stat.st_mtime
            assert watcher._last_inode == stat.st_ino

    def test_directory_watching_cross_platform_behavior(self):
        """Test directory watching behavior across platforms."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            watcher = PathWatcher(tmp_dir)
            initial_mtime = watcher._last_mtime

            # Test 1: Create a file in the directory - this should change directory mtime
            test_file = os.path.join(tmp_dir, "test.txt")
            time.sleep(0.1)  # Ensure time difference
            with open(test_file, "w") as f:
                f.write("test content")

            # Check if directory mtime changed
            new_stat = os.stat(tmp_dir)
            print(f"After file creation - Initial: {initial_mtime}, New: {new_stat.st_mtime}")
            print(f"Directory mtime changed on file creation: {new_stat.st_mtime != initial_mtime}")

            # Test 2: Modify existing file content - this should NOT change directory mtime
            modify_mtime = new_stat.st_mtime
            time.sleep(0.1)  # Ensure time difference
            with open(test_file, "w") as f:
                f.write("modified content - much longer text")

            # Check if directory mtime changed after content modification
            final_stat = os.stat(tmp_dir)
            print(f"After file modification - Before: {modify_mtime}, After: {final_stat.st_mtime}")
            print(f"Directory mtime changed on file modification: {final_stat.st_mtime != modify_mtime}")


class TestPathWatcherChangeDetection:
    """Test PathWatcher change detection functionality."""

    def test_path_watcher_detects_file_mtime_changes(self):
        """PathWatcher detects file mtime changes."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write("initial content")
            tmp_file.flush()

            watcher = PathWatcher(tmp_file.name)

            # Modify file content
            time.sleep(0.1)  # Ensure time difference
            with open(tmp_file.name, "w") as f:
                f.write("modified content")

            # Check if change is detected
            has_changed = watcher.has_changed()
            assert has_changed is True

            # Clean up
            os.unlink(tmp_file.name)

    def test_path_watcher_detects_file_inode_changes(self):
        """PathWatcher detects file inode changes (rename/replace)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write("initial content")
            tmp_file.flush()
            original_name = tmp_file.name

            watcher = PathWatcher(original_name)

            # Create new file and replace original (simulates editor save behavior)
            temp_name = original_name + ".tmp"
            with open(temp_name, "w") as f:
                f.write("replaced content")

            time.sleep(0.1)  # Ensure time difference
            os.rename(temp_name, original_name)

            # Check if change is detected
            has_changed = watcher.has_changed()
            assert has_changed is True

            # Clean up
            os.unlink(original_name)

    def test_path_watcher_detects_directory_mtime_changes(self):
        """PathWatcher detects directory mtime changes."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            watcher = PathWatcher(tmp_dir)

            # Add a file to the directory
            time.sleep(0.1)  # Ensure time difference
            test_file = os.path.join(tmp_dir, "new_file.txt")
            with open(test_file, "w") as f:
                f.write("new file content")

            # Check if change is detected
            has_changed = watcher.has_changed()
            assert has_changed is True

    def test_path_watcher_ignores_unchanged_files(self):
        """PathWatcher ignores unchanged files."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            watcher = PathWatcher(tmp_file.name)

            # Check multiple times without changes
            assert watcher.has_changed() is False
            assert watcher.has_changed() is False
            assert watcher.has_changed() is False


class TestPathWatcherCallbackSystem:
    """Test PathWatcher callback functionality."""

    def test_path_watcher_accepts_callback_function_on_instantiation(self):
        """PathWatcher accepts callback function on instantiation."""
        callback = Mock()

        with tempfile.NamedTemporaryFile() as tmp_file:
            watcher = PathWatcher(tmp_file.name, callback=callback)
            assert callback in watcher._callbacks

    def test_callback_is_invoked_when_changes_are_detected(self):
        """Callback is invoked when changes are detected."""
        callback = Mock()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write("initial content")
            tmp_file.flush()

            watcher = PathWatcher(tmp_file.name, callback=callback)

            # Modify file content
            time.sleep(0.1)  # Ensure time difference
            with open(tmp_file.name, "w") as f:
                f.write("modified content")

            # Check for changes (should trigger callback)
            watcher.has_changed()

            # Verify callback was called
            callback.assert_called_once_with(tmp_file.name)

            # Clean up
            os.unlink(tmp_file.name)

    def test_callback_receives_path_as_parameter(self):
        """Callback receives path as parameter."""
        callback = Mock()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write("initial content")
            tmp_file.flush()
            original_name = tmp_file.name

            watcher = PathWatcher(original_name, callback=callback)

            # Create new file and replace original (inode change)
            temp_name = original_name + ".tmp"
            with open(temp_name, "w") as f:
                f.write("replaced content")

            time.sleep(0.1)  # Ensure time difference
            os.rename(temp_name, original_name)

            # Check for changes (should trigger callback)
            watcher.has_changed()

            # Verify callback was called with correct parameters
            callback.assert_called_once_with(original_name)

            # Clean up
            os.unlink(original_name)

    def test_multiple_callbacks_can_be_registered(self):
        """Multiple callbacks can be registered."""
        callback1 = Mock()
        callback2 = Mock()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write("initial content")
            tmp_file.flush()

            watcher = PathWatcher(tmp_file.name, callback=callback1)
            watcher.add_callback(callback2)

            # Modify file content
            time.sleep(0.1)  # Ensure time difference
            with open(tmp_file.name, "w") as f:
                f.write("modified content")

            # Check for changes (should trigger both callbacks)
            watcher.has_changed()

            # Verify both callbacks were called
            callback1.assert_called_once_with(tmp_file.name)
            callback2.assert_called_once_with(tmp_file.name)

            # Clean up
            os.unlink(tmp_file.name)

    def test_callback_exceptions_dont_crash_watcher(self):
        """Callback exceptions don't crash watcher."""

        def failing_callback(path):
            raise ValueError("Callback error")

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write("initial content")
            tmp_file.flush()

            watcher = PathWatcher(tmp_file.name, callback=failing_callback)

            # Modify file content
            time.sleep(0.1)  # Ensure time difference
            with open(tmp_file.name, "w") as f:
                f.write("modified content")

            # Check for changes (callback should fail but not crash)
            has_changed = watcher.has_changed()
            assert has_changed is True  # Change should still be detected

            # Clean up
            os.unlink(tmp_file.name)


class TestPathWatcherAsyncTaskManagement:
    """Test PathWatcher async task management functionality."""

    @pytest.mark.asyncio
    async def test_path_watcher_doesnt_start_monitoring_until_start_called(self):
        """PathWatcher doesn't start monitoring until start() is called."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            watcher = PathWatcher(tmp_file.name, poll_interval=0.1)

            # Should not be running initially
            assert watcher._task is None
            assert watcher.is_running() is False

    @pytest.mark.asyncio
    async def test_start_creates_and_runs_asyncio_task(self):
        """start() creates and runs asyncio task."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            watcher = PathWatcher(tmp_file.name, poll_interval=0.1)

            # Start monitoring
            await watcher.start()

            # Should now be running
            assert watcher._task is not None
            assert watcher.is_running() is True

            # Clean up
            await watcher.stop()

    @pytest.mark.asyncio
    async def test_multiple_start_calls_dont_create_duplicate_tasks(self):
        """Multiple start() calls don't create duplicate tasks."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            watcher = PathWatcher(tmp_file.name, poll_interval=0.1)

            # Start monitoring multiple times
            await watcher.start()
            first_task = watcher._task

            await watcher.start()  # Should not create new task
            second_task = watcher._task

            # Should be the same task
            assert first_task is second_task
            assert watcher.is_running() is True

            # Clean up
            await watcher.stop()

    @pytest.mark.asyncio
    async def test_task_polls_at_configurable_intervals(self):
        """Task polls at configurable intervals."""
        callback = Mock()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write("initial content")
            tmp_file.flush()

            # Create watcher with short poll interval
            watcher = PathWatcher(tmp_file.name, callback=callback, poll_interval=0.05)

            # Start monitoring
            await watcher.start()

            # Modify file after a short delay
            await asyncio.sleep(0.02)
            with open(tmp_file.name, "w") as f:
                f.write("modified content")

            # Wait for polling to detect change
            await asyncio.sleep(0.1)

            # Callback should have been invoked
            callback.assert_called_once_with(tmp_file.name)

            # Clean up
            await watcher.stop()
            os.unlink(tmp_file.name)


class TestPathWatcherSingleInstanceManagement:
    """Test PathWatcher single instance management."""

    @pytest.mark.asyncio
    async def test_only_one_path_watcher_per_path_allowed(self):
        """Only one PathWatcher per path is allowed."""
        from mcp_core.watcher_registry import get_global_registry

        registry = get_global_registry()

        with tempfile.NamedTemporaryFile() as tmp_file:
            # Create first watcher and register it
            watcher1 = PathWatcher(tmp_file.name)
            await registry.register(tmp_file.name, watcher1)

            # Try to create second watcher for same path
            watcher2 = PathWatcher(tmp_file.name)
            with pytest.raises(ValueError, match="PathWatcher already exists"):
                await registry.register(tmp_file.name, watcher2)

            # Clean up
            await registry.unregister(tmp_file.name)

    @pytest.mark.asyncio
    async def test_attempting_duplicate_watcher_raises_appropriate_error(self):
        """Attempting duplicate watcher raises appropriate error."""
        from mcp_core.watcher_registry import WatcherRegistry

        registry = WatcherRegistry()

        with tempfile.NamedTemporaryFile() as tmp_file:
            # Register first watcher
            watcher1 = PathWatcher(tmp_file.name)
            await registry.register(tmp_file.name, watcher1)

            # Try to register second watcher
            watcher2 = PathWatcher(tmp_file.name)
            with pytest.raises(ValueError) as exc_info:
                await registry.register(tmp_file.name, watcher2)

            assert "PathWatcher already exists" in str(exc_info.value)
            assert tmp_file.name in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_watcher_registry_tracks_active_instances(self):
        """Watcher registry tracks active instances."""
        from mcp_core.watcher_registry import WatcherRegistry

        registry = WatcherRegistry()

        with tempfile.NamedTemporaryFile() as tmp_file1, tempfile.NamedTemporaryFile() as tmp_file2:
            # Register watchers for different paths
            watcher1 = PathWatcher(tmp_file1.name)
            watcher2 = PathWatcher(tmp_file2.name)

            await registry.register(tmp_file1.name, watcher1)
            await registry.register(tmp_file2.name, watcher2)

            # Verify both are tracked
            assert registry.get(tmp_file1.name) is watcher1
            assert registry.get(tmp_file2.name) is watcher2

            # Clean up
            await registry.unregister(tmp_file1.name)
            await registry.unregister(tmp_file2.name)

    @pytest.mark.asyncio
    async def test_registry_cleanup_when_watchers_are_stopped(self):
        """Registry cleanup when watchers are stopped."""
        from mcp_core.watcher_registry import WatcherRegistry

        registry = WatcherRegistry()

        with tempfile.NamedTemporaryFile() as tmp_file:
            # Register and start watcher
            watcher = PathWatcher(tmp_file.name)
            await registry.register(tmp_file.name, watcher)
            await watcher.start()

            # Verify it's tracked
            assert registry.get(tmp_file.name) is watcher

            # Stop watcher and cleanup
            await watcher.stop()
            await registry.cleanup_stopped()

            # Should be removed from registry
            assert registry.get(tmp_file.name) is None

    """Test PathWatcher task lifecycle management."""

    @pytest.mark.asyncio
    async def test_stop_method_cleanly_terminates_monitoring_task(self):
        """stop() method cleanly terminates monitoring task."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            watcher = PathWatcher(tmp_file.name, poll_interval=0.1)

            # Start monitoring
            await watcher.start()
            assert watcher.is_running() is True

            # Stop monitoring
            await watcher.stop()
            assert watcher.is_running() is False
            assert watcher._task is None

    @pytest.mark.asyncio
    async def test_task_can_be_restarted_after_being_stopped(self):
        """Task can be restarted after being stopped."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            watcher = PathWatcher(tmp_file.name, poll_interval=0.1)

            # Start, stop, then start again
            await watcher.start()
            first_task = watcher._task
            assert watcher.is_running() is True

            await watcher.stop()
            assert watcher.is_running() is False

            await watcher.start()
            second_task = watcher._task
            assert watcher.is_running() is True

            # Should be different tasks
            assert first_task is not second_task

            # Clean up
            await watcher.stop()

    @pytest.mark.asyncio
    async def test_path_watcher_handles_task_exceptions_gracefully(self):
        """PathWatcher handles task exceptions gracefully."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            watcher = PathWatcher(tmp_file.name, poll_interval=0.1)

            # Start monitoring
            await watcher.start()
            original_task = watcher._task

            # Force task to raise an exception by deleting the file
            os.unlink(tmp_file.name)

            # Wait a bit for the task to encounter the error
            await asyncio.sleep(0.2)

            # Task should still be the same (not crashed)
            # The exception should be handled in the monitoring loop
            assert watcher._task is original_task

            # Clean up
            await watcher.stop()
