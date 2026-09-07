"""Watcher registry behaviour across registration, reuse and cleanup."""

import pytest

from mcp_guide.core.path_watcher import PathWatcher
from mcp_guide.core.watcher_registry import WatcherRegistry, get_global_registry


@pytest.mark.anyio
async def test_registry_rejects_duplicate_paths_and_unregisters_only_the_selected_watcher(tmp_path):
    registry = WatcherRegistry()
    first_path, second_path = str(tmp_path / "first"), str(tmp_path / "second")
    first, second = PathWatcher(first_path), PathWatcher(second_path)
    assert await registry.get(first_path) is None
    await registry.register(first_path, first)
    await registry.register(second_path, second)
    with pytest.raises(ValueError, match="PathWatcher already exists"):
        await registry.register(str(tmp_path) + "/./first", PathWatcher(first_path))
    assert await registry.get(first_path) is first
    assert await registry.get(second_path) is second
    await registry.unregister(first_path)
    assert await registry.get(first_path) is None
    assert await registry.get(second_path) is second


@pytest.mark.anyio
async def test_get_or_create_reuses_the_registered_watcher(tmp_path):
    registry = WatcherRegistry()
    path = str(tmp_path / "watched")
    created = PathWatcher(path)
    assert await registry.get_or_create(path, lambda: created) is created
    assert await registry.get(path) is created

    def unexpected_factory():
        pytest.fail("An existing watcher must not be recreated")

    assert await registry.get_or_create(path, unexpected_factory) is created


@pytest.mark.anyio
async def test_cleanup_removes_stopped_watchers_but_retains_running_watchers(tmp_path):
    registry = WatcherRegistry()
    active_path, idle_path = tmp_path / "active", tmp_path / "idle"
    active_path.touch()
    idle_path.touch()
    active, idle = PathWatcher(active_path), PathWatcher(idle_path)
    await registry.register(str(active_path), active)
    await registry.register(str(idle_path), idle)
    await active.start()
    try:
        await registry.cleanup_stopped()
        assert await registry.get(str(active_path)) is active
        assert await registry.get(str(idle_path)) is None
    finally:
        await active.stop()
    await registry.cleanup_stopped()
    assert await registry.get(str(active_path)) is None


def test_global_registry_is_shared_between_consumers():
    assert get_global_registry() is get_global_registry()
