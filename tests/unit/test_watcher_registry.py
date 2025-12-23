"""Tests for WatcherRegistry functionality."""

import tempfile

import pytest

from mcp_core.path_watcher import PathWatcher
from mcp_core.watcher_registry import WatcherRegistry, get_global_registry


class TestWatcherRegistry:
    """Test WatcherRegistry functionality."""

    @pytest.mark.asyncio
    async def test_registry_prevents_duplicate_watchers_for_same_path(self):
        """Registry prevents duplicate watchers for same path."""
        registry = WatcherRegistry()

        with tempfile.NamedTemporaryFile() as tmp_file:
            # Register first watcher
            watcher1 = PathWatcher(tmp_file.name)
            await registry.register(tmp_file.name, watcher1)

            # Try to register second watcher for same path
            watcher2 = PathWatcher(tmp_file.name)
            with pytest.raises(ValueError, match="PathWatcher already exists"):
                await registry.register(tmp_file.name, watcher2)

    @pytest.mark.asyncio
    async def test_registry_allows_different_paths(self):
        """Registry allows watchers for different paths."""
        registry = WatcherRegistry()

        with tempfile.NamedTemporaryFile() as tmp_file1, tempfile.NamedTemporaryFile() as tmp_file2:
            # Register watchers for different paths
            watcher1 = PathWatcher(tmp_file1.name)
            watcher2 = PathWatcher(tmp_file2.name)

            await registry.register(tmp_file1.name, watcher1)
            await registry.register(tmp_file2.name, watcher2)

            # Both should be registered successfully
            assert registry.get(tmp_file1.name) is watcher1
            assert registry.get(tmp_file2.name) is watcher2

    @pytest.mark.asyncio
    async def test_registry_get_returns_existing_watcher(self):
        """Registry get() returns existing watcher."""
        registry = WatcherRegistry()

        with tempfile.NamedTemporaryFile() as tmp_file:
            watcher = PathWatcher(tmp_file.name)
            await registry.register(tmp_file.name, watcher)

            retrieved = registry.get(tmp_file.name)
            assert retrieved is watcher

    @pytest.mark.asyncio
    async def test_registry_get_returns_none_for_nonexistent_path(self):
        """Registry get() returns None for nonexistent path."""
        registry = WatcherRegistry()

        result = registry.get("/nonexistent/path")
        assert result is None

    @pytest.mark.asyncio
    async def test_registry_unregister_removes_watcher(self):
        """Registry unregister() removes watcher."""
        registry = WatcherRegistry()

        with tempfile.NamedTemporaryFile() as tmp_file:
            watcher = PathWatcher(tmp_file.name)
            await registry.register(tmp_file.name, watcher)

            # Verify it's registered
            assert registry.get(tmp_file.name) is watcher

            # Unregister and verify it's gone
            await registry.unregister(tmp_file.name)
            assert registry.get(tmp_file.name) is None

    @pytest.mark.asyncio
    async def test_registry_cleanup_stopped_removes_inactive_watchers(self):
        """Registry cleanup_stopped() removes inactive watchers."""
        registry = WatcherRegistry()

        with tempfile.NamedTemporaryFile() as tmp_file1, tempfile.NamedTemporaryFile() as tmp_file2:
            # Register two watchers
            watcher1 = PathWatcher(tmp_file1.name)
            watcher2 = PathWatcher(tmp_file2.name)

            await registry.register(tmp_file1.name, watcher1)
            await registry.register(tmp_file2.name, watcher2)

            # Start one watcher
            await watcher1.start()

            # Clean up stopped watchers
            await registry.cleanup_stopped()

            # Running watcher should remain, stopped one should be removed
            assert registry.get(tmp_file1.name) is watcher1
            assert registry.get(tmp_file2.name) is None

            # Clean up
            await watcher1.stop()

    @pytest.mark.asyncio
    async def test_get_or_create_creates_new_watcher(self):
        """get_or_create() creates new watcher when none exists."""
        registry = WatcherRegistry()

        with tempfile.NamedTemporaryFile() as tmp_file:
            factory_called = False

            def factory():
                nonlocal factory_called
                factory_called = True
                return PathWatcher(tmp_file.name)

            watcher = await registry.get_or_create(tmp_file.name, factory)

            assert factory_called is True
            assert isinstance(watcher, PathWatcher)
            assert registry.get(tmp_file.name) is watcher

    @pytest.mark.asyncio
    async def test_get_or_create_returns_existing_watcher(self):
        """get_or_create() returns existing watcher if it exists."""
        registry = WatcherRegistry()

        with tempfile.NamedTemporaryFile() as tmp_file:
            # Register existing watcher
            existing_watcher = PathWatcher(tmp_file.name)
            await registry.register(tmp_file.name, existing_watcher)

            # get_or_create should return existing watcher
            def factory():
                return PathWatcher(tmp_file.name)

            result = await registry.get_or_create(tmp_file.name, factory)
            assert result is existing_watcher

    def test_get_global_registry_returns_singleton(self):
        """get_global_registry() returns singleton instance."""
        registry1 = get_global_registry()
        registry2 = get_global_registry()

        assert registry1 is registry2
        assert isinstance(registry1, WatcherRegistry)
