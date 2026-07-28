"""Tests for project-scoped task lifecycle restart."""

import asyncio
from typing import TYPE_CHECKING, Any, cast

import pytest

from mcp_guide.result import Result
from mcp_guide.task_manager import EventType, TaskManager
from mcp_guide.task_manager.manager import EventResult

if TYPE_CHECKING:
    from mcp_guide.session import Session


@pytest.fixture(autouse=True)
def clear_task_registry() -> None:
    """Keep project task registration isolated per test."""
    from mcp_guide.decorators import clear_registered_tasks_for_testing

    clear_registered_tasks_for_testing()


class _ProjectSession:
    """Small session stub that exposes a project name for assertions."""

    def __init__(self, name: str) -> None:
        self.name = name


def _session(name: str) -> "Session":
    """Return a minimal session stub cast for lifecycle API tests."""
    return cast("Session", _ProjectSession(name))


class _ProjectTask:
    """Project-scoped task stub with explicit start/stop hooks."""

    started_for: list[str] = []
    stopped_for: list[str] = []

    def __init__(self) -> None:
        self.session_name: str | None = None

    def get_name(self) -> str:
        return f"ProjectTask:{self.session_name}"

    async def start(self, task_manager: TaskManager, session: _ProjectSession) -> bool:
        self.session_name = session.name
        self.started_for.append(session.name)
        task_manager.subscribe(self, EventType.FS_FILE_CONTENT)
        return True

    async def stop(self, task_manager: TaskManager) -> None:
        if self.session_name:
            self.stopped_for.append(self.session_name)

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult | None:
        return None

    async def on_tool(self) -> None:
        pass


class _InactiveProjectTask(_ProjectTask):
    """Task that chooses not to subscribe for the current project context."""

    async def start(self, task_manager: TaskManager, session: _ProjectSession) -> bool:
        self.session_name = session.name
        self.started_for.append(session.name)
        return False


class _FailingStopProjectTask(_ProjectTask):
    """Task whose stop hook fails after it has been active."""

    async def stop(self, task_manager: TaskManager) -> None:
        raise RuntimeError("stop failed")


class _FailingStartProjectTask(_ProjectTask):
    """Task whose start hook fails before activation completes."""

    async def start(self, task_manager: TaskManager, session: _ProjectSession) -> bool:
        self.session_name = session.name
        self.started_for.append(session.name)
        task_manager.subscribe(self, EventType.FS_FILE_CONTENT)
        raise RuntimeError("start failed")


class _CancelledStartProjectTask(_ProjectTask):
    """Task whose start hook is cancelled."""

    async def start(self, task_manager: TaskManager, session: _ProjectSession) -> bool:
        raise asyncio.CancelledError


class _CancelledStopProjectTask(_ProjectTask):
    """Task whose stop hook is cancelled."""

    async def stop(self, task_manager: TaskManager) -> None:
        raise asyncio.CancelledError


@pytest.fixture(autouse=True)
def reset_project_task_state() -> None:
    """Reset class-level assertion state."""
    _ProjectTask.started_for = []
    _ProjectTask.stopped_for = []
    _InactiveProjectTask.started_for = []
    _InactiveProjectTask.stopped_for = []
    _FailingStopProjectTask.started_for = []
    _FailingStopProjectTask.stopped_for = []
    _FailingStartProjectTask.started_for = []
    _FailingStartProjectTask.stopped_for = []
    _CancelledStartProjectTask.started_for = []
    _CancelledStartProjectTask.stopped_for = []
    _CancelledStopProjectTask.started_for = []
    _CancelledStopProjectTask.stopped_for = []


class TestProjectTaskLifecycle:
    """TaskManager restarts project-scoped registered task classes."""

    @pytest.mark.anyio
    async def test_initial_project_bind_starts_registered_task(self) -> None:
        """Registered task classes start after a project context is supplied."""
        from mcp_guide.decorators import task_register

        task_register(_ProjectTask)
        task_manager = TaskManager()

        await task_manager.restart_project_tasks(_session("alpha"))
        task = task_manager.get_task_by_type(_ProjectTask)

        assert _ProjectTask.started_for == ["alpha"]
        assert task_manager.get_subscription_count() == 1
        assert task is not None
        assert task.session_name == "alpha"

    @pytest.mark.anyio
    async def test_inactive_task_is_not_kept_active(self) -> None:
        """A task class can decide not to subscribe for the current project."""
        from mcp_guide.decorators import task_register

        task_register(_InactiveProjectTask)
        task_manager = TaskManager()

        await task_manager.restart_project_tasks(_session("alpha"))

        assert _InactiveProjectTask.started_for == ["alpha"]
        assert task_manager.get_subscription_count() == 0
        assert task_manager.get_task_by_type(_InactiveProjectTask) is None

    @pytest.mark.anyio
    async def test_project_switch_stops_old_instance_and_starts_fresh_instance(self) -> None:
        """Project switches replace all active project-scoped task instances."""
        from mcp_guide.decorators import task_register

        task_register(_ProjectTask)
        task_manager = TaskManager()

        await task_manager.restart_project_tasks(_session("alpha"))
        first = task_manager.get_task_by_type(_ProjectTask)

        await task_manager.restart_project_tasks(_session("beta"))
        second = task_manager.get_task_by_type(_ProjectTask)

        assert first is not second
        assert _ProjectTask.started_for == ["alpha", "beta"]
        assert _ProjectTask.stopped_for == ["alpha"]
        assert second is not None
        assert second.session_name == "beta"
        assert task_manager.get_subscription_count() == 1

    @pytest.mark.anyio
    async def test_config_change_restarts_tasks_for_current_project(self) -> None:
        """Config changes restart task-owned activation policy."""
        from mcp_guide.decorators import task_register

        task_register(_ProjectTask)
        task_manager = TaskManager()
        session = _session("alpha")

        await task_manager.restart_project_tasks(session)
        first = task_manager.get_task_by_type(_ProjectTask)
        await task_manager.on_config_changed(session)
        second = task_manager.get_task_by_type(_ProjectTask)

        assert first is not second
        assert _ProjectTask.started_for == ["alpha", "alpha"]
        assert _ProjectTask.stopped_for == ["alpha"]
        assert task_manager.get_subscription_count() == 1

    @pytest.mark.anyio
    async def test_concurrent_restarts_complete_without_duplicate_subscriptions(self) -> None:
        """Concurrent lifecycle triggers serialize without duplicate subscribers."""
        from mcp_guide.decorators import task_register

        task_register(_ProjectTask)
        task_manager = TaskManager()

        await asyncio.gather(
            task_manager.restart_project_tasks(_session("alpha")),
            task_manager.restart_project_tasks(_session("beta")),
        )

        task = task_manager.get_task_by_type(_ProjectTask)
        assert task_manager.get_subscription_count() == 1
        assert task is not None
        assert task.session_name in {"alpha", "beta"}

    @pytest.mark.anyio
    async def test_restart_clears_project_scoped_cache_entries(self) -> None:
        """Lifecycle restart clears volatile cache values from the previous project."""
        task_manager = TaskManager()
        task_manager.set_cached_data("workflow_state", {"phase": "discussion"})
        task_manager.set_cached_data("openspec_version", "1.2.3")
        task_manager.set_cached_data("client_os_info", {"os": "test"})
        task_manager.set_cached_data("unrelated", "keep")

        await task_manager.restart_project_tasks(_session("alpha"))

        assert task_manager.get_cached_data("workflow_state") is None
        assert task_manager.get_cached_data("openspec_version") == "1.2.3"
        assert task_manager.get_cached_data("client_os_info") is None
        assert task_manager.get_cached_data("unrelated") == "keep"
        assert "workflow_state" not in task_manager._cache
        assert "openspec_version" in task_manager._cache
        assert "client_os_info" not in task_manager._cache
        assert "unrelated" in task_manager._cache

    @pytest.mark.anyio
    async def test_restart_clears_queued_instructions(self) -> None:
        """Lifecycle restart does not leak previous-project instructions."""
        task_manager = TaskManager()
        await task_manager.queue_instruction("regular stale instruction")
        tracked_id = await task_manager.queue_instruction_with_ack("tracked stale instruction")

        await task_manager.restart_project_tasks(_session("alpha"))
        result = await task_manager.process_result(Result.ok("unchanged"))

        assert task_manager._pending_instructions == []
        assert tracked_id not in task_manager._tracked_instructions
        assert result.additional_agent_instructions is None

    @pytest.mark.anyio
    async def test_stop_failure_still_unsubscribes_stale_instance(self, caplog) -> None:
        """A failing stop hook cannot leave old project subscriptions active."""
        from mcp_guide.decorators import task_register

        task_register(_FailingStopProjectTask)
        task_manager = TaskManager()

        await task_manager.restart_project_tasks(_session("alpha"))
        first = task_manager.get_task_by_type(_FailingStopProjectTask)

        await task_manager.restart_project_tasks(_session("beta"))
        second = task_manager.get_task_by_type(_FailingStopProjectTask)

        assert first is not second
        assert second is not None
        assert second.session_name == "beta"
        assert task_manager.get_subscription_count() == 1
        assert "Error stopping project-scoped task" in caplog.text

    @pytest.mark.anyio
    async def test_unexpected_stop_failure_does_not_block_remaining_stops(self, monkeypatch, caplog) -> None:
        """An unexpected stop helper failure cannot block other stale task stops."""
        from mcp_guide.decorators import task_register

        task_register(_ProjectTask)
        task_manager = TaskManager()
        first = _ProjectTask()
        second = _ProjectTask()
        await first.start(task_manager, _ProjectSession("first"))
        await second.start(task_manager, _ProjectSession("second"))
        task_manager._active_project_tasks = {_ProjectTask: first, _InactiveProjectTask: second}
        original_stop = task_manager._stop_project_task

        async def stop_with_one_unexpected_failure(task):
            if task is first:
                raise RuntimeError("unexpected stop helper failure")
            await original_stop(task)

        monkeypatch.setattr(task_manager, "_stop_project_task", stop_with_one_unexpected_failure)

        await task_manager.restart_project_tasks(_session("next"))

        assert "second" in _ProjectTask.stopped_for
        assert "Error stopping project-scoped task" in caplog.text

    @pytest.mark.anyio
    async def test_start_failure_does_not_block_other_registered_tasks(self, caplog) -> None:
        """A failing start hook cannot abort lifecycle restart for later tasks."""
        from mcp_guide.decorators import task_register

        task_register(_FailingStartProjectTask)
        task_register(_ProjectTask)
        task_manager = TaskManager()

        await task_manager.restart_project_tasks(_session("alpha"))

        assert task_manager.get_task_by_type(_FailingStartProjectTask) is None
        task = task_manager.get_task_by_type(_ProjectTask)
        assert task is not None
        assert task.session_name == "alpha"
        assert task_manager.get_subscription_count() == 1
        assert "Error starting project-scoped task" in caplog.text

    @pytest.mark.anyio
    async def test_start_cancellation_propagates(self) -> None:
        """Task start cancellation is not swallowed as a startup failure."""
        from mcp_guide.decorators import task_register

        task_register(_CancelledStartProjectTask)
        task_manager = TaskManager()

        with pytest.raises(asyncio.CancelledError):
            await task_manager.restart_project_tasks(_session("alpha"))

        assert task_manager.get_task_by_type(_CancelledStartProjectTask) is None

    @pytest.mark.anyio
    async def test_stop_cancellation_propagates_after_unsubscribe(self) -> None:
        """Task stop cancellation propagates while still clearing stale subscriptions."""
        from mcp_guide.decorators import task_register

        task_register(_CancelledStopProjectTask)
        task_manager = TaskManager()

        await task_manager.restart_project_tasks(_session("alpha"))

        with pytest.raises(asyncio.CancelledError):
            await task_manager.restart_project_tasks(_session("beta"))

        assert task_manager.get_task_by_type(_CancelledStopProjectTask) is None
        assert task_manager.get_subscription_count() == 0

    @pytest.mark.anyio
    async def test_timer_start_failure_cleans_up_started_project_tasks(self, monkeypatch) -> None:
        """Timer startup failure after publication stops and unregisters started tasks."""
        from mcp_guide.decorators import task_register

        task_register(_ProjectTask)
        task_manager = TaskManager()

        async def fail_timer_start() -> None:
            raise RuntimeError("timer startup failed")

        monkeypatch.setattr(task_manager, "start", fail_timer_start)

        with pytest.raises(RuntimeError, match="timer startup failed"):
            await task_manager.restart_project_tasks(_session("alpha"))

        assert _ProjectTask.stopped_for == ["alpha"]
        assert task_manager.get_task_by_type(_ProjectTask) is None
        assert task_manager.get_subscription_count() == 0
        assert task_manager._active_project_tasks == {}

    @pytest.mark.anyio
    async def test_cleanup_finishes_after_stop_cancellation(self) -> None:
        """Cancellation from one stop hook does not skip later task cleanup."""
        task_manager = TaskManager()
        cancelled = _CancelledStopProjectTask()
        remaining = _ProjectTask()
        await cancelled.start(task_manager, _ProjectSession("cancelled"))
        await remaining.start(task_manager, _ProjectSession("remaining"))

        with pytest.raises(asyncio.CancelledError):
            await task_manager._cleanup_started_project_tasks([cancelled, remaining])

        assert _ProjectTask.stopped_for == ["remaining"]
        assert task_manager.get_subscription_count() == 0

    @pytest.mark.anyio
    async def test_start_failure_unsubscribe_failure_does_not_block_later_tasks(self, monkeypatch, caplog) -> None:
        """A failed startup cleanup unsubscribe cannot abort later task startup."""
        from mcp_guide.decorators import task_register

        task_register(_FailingStartProjectTask)
        task_register(_ProjectTask)
        task_manager = TaskManager()
        original_unsubscribe = task_manager.unsubscribe

        async def unsubscribe_with_one_failure(task):
            if isinstance(task, _FailingStartProjectTask):
                raise RuntimeError("unsubscribe failed")
            await original_unsubscribe(task)

        monkeypatch.setattr(task_manager, "unsubscribe", unsubscribe_with_one_failure)

        await task_manager.restart_project_tasks(_session("alpha"))

        task = task_manager.get_task_by_type(_ProjectTask)
        assert task is not None
        assert task.session_name == "alpha"
        assert "Error unsubscribing failed project-scoped task" in caplog.text
