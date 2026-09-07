"""Startup failure and lazy flag resolution through real lifecycle objects."""

import pytest
from tests.helpers import create_bound_test_session

from mcp_guide.runtime import create_runtime
from mcp_guide.task_manager import TaskManager


@pytest.mark.anyio
async def test_failed_startup_leaves_runtime_unstarted():
    async def failing_service():
        raise RuntimeError("Service unavailable")

    runtime = create_runtime(lambda _owner: object(), on_start=failing_service)
    with pytest.raises(RuntimeError, match="Service unavailable"):
        await runtime.start()
    assert not runtime.started
    await runtime.stop()


@pytest.mark.anyio
async def test_flag_cache_follows_configuration_changes_and_explicit_project(runtime):
    runtime.configuration_service().config_file.write_text("feature_flags: {}\nprojects: {}\n")
    first = await create_bound_test_session(runtime, "first")
    second = await create_bound_test_session(runtime, "second")
    await first.project_flags().set("example", True)
    await second.project_flags().set("example", False)
    manager = TaskManager(first)
    try:
        initial = await manager.resolved_flags()
        assert initial == {"example": True}
        assert await manager.resolved_flags() is initial
        assert await manager.requires_flag("example")
        assert not await manager.requires_flag("missing")
        await first.project_flags().set("example", False)
        assert not await manager.requires_flag("example")
        await first.project_flags().set("example", True)
        assert await manager.requires_flag("example")
        await manager.on_project_changed(second, "first", "second")
        assert await manager.resolved_flags(second) == {"example": False}
        assert not await manager.requires_flag("example", second)
    finally:
        await manager.cleanup()
