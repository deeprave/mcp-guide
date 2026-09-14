"""Tests for project-scoped task lifecycle restart."""

import asyncio
from contextlib import nullcontext
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import Mock

import pytest

from mcp_guide.result import Result
from mcp_guide.task_manager import EventType, TaskActivation, TaskManager
from mcp_guide.task_manager.manager import EventResult

if TYPE_CHECKING:
    from mcp_guide.session import Session


@pytest.fixture(autouse=True)
def clear_task_registry():
    """Keep task registration isolated and restore imported production tasks."""
    from mcp_guide.decorators import (
        clear_registered_tasks_for_testing,
        get_registered_task_classes,
        task_register,
    )

    registered = get_registered_task_classes()
    clear_registered_tasks_for_testing()
    try:
        yield
    finally:
        clear_registered_tasks_for_testing()
        for task_class in registered:
            task_register(task_class)


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
        self.activation: TaskActivation | None = None

    def get_name(self) -> str:
        return f"ProjectTask:{self.session_name}"

    async def start(self, activation: TaskActivation) -> bool:
        self.activation = activation
        self.session_name = activation.session.name
        self.started_for.append(activation.session.name)
        activation.subscribe(EventType.FS_FILE_CONTENT)
        return True

    async def stop(self) -> None:
        if self.session_name:
            self.stopped_for.append(self.session_name)

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult | None:
        return None

    async def on_tool(self) -> None:
        pass


class _InjectedManagerProjectTask(_ProjectTask):
    """Task double that retains its activation instead of a manager."""

    def __init__(self) -> None:
        super().__init__()
        self.constructed_with: TaskActivation | None = None

    async def start(self, activation: TaskActivation) -> bool:
        self.constructed_with = activation
        return await super().start(activation)


class _InactiveProjectTask(_ProjectTask):
    """Task that chooses not to subscribe for the current project context."""

    async def start(self, activation: TaskActivation) -> bool:
        self.session_name = activation.session.name
        self.started_for.append(activation.session.name)
        return False


class _FailingStopProjectTask(_ProjectTask):
    """Task whose stop hook fails after it has been active."""

    async def stop(self) -> None:
        raise RuntimeError("stop failed")


class _FailingStartProjectTask(_ProjectTask):
    """Task whose start hook fails before activation completes."""

    async def start(self, activation: TaskActivation) -> bool:
        self.session_name = activation.session.name
        self.started_for.append(activation.session.name)
        activation.subscribe(EventType.FS_FILE_CONTENT)
        raise RuntimeError("start failed")


class _CancelledStartProjectTask(_ProjectTask):
    """Task whose start hook is cancelled."""

    async def start(self, activation: TaskActivation) -> bool:
        await super().start(activation)
        raise asyncio.CancelledError


class _CancelledStopProjectTask(_ProjectTask):
    """Task whose stop hook is cancelled."""

    async def stop(self) -> None:
        raise asyncio.CancelledError


class _BlockingStopProjectTask(_ProjectTask):
    """Task double that permits a second restart while its stop hook waits."""

    stop_started: asyncio.Event | None = None
    allow_stop: asyncio.Event | None = None

    async def stop(self) -> None:
        assert self.stop_started is not None
        assert self.allow_stop is not None
        self.stop_started.set()
        await self.allow_stop.wait()
        await super().stop()


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
        task_manager = TaskManager(session=Mock(template_cache=Mock(), work=nullcontext))

        await task_manager.restart_project_tasks(_session("alpha"))
        task = task_manager.get_task_by_type(_ProjectTask)

        assert _ProjectTask.started_for == ["alpha"]
        assert task_manager.get_subscription_count() == 1
        assert task is not None
        assert task.session_name == "alpha"

    @pytest.mark.anyio
    async def test_project_task_receives_activation_for_owned_state(self) -> None:
        """A project task receives one activation instead of the general manager."""
        from mcp_guide.decorators import task_register

        class ActivationOnlyTask:
            def __init__(self) -> None:
                self.activation: Any | None = None

            def get_name(self) -> str:
                return "ActivationOnlyTask"

            async def start(self, activation: Any) -> bool:
                self.activation = activation
                activation.set_cached_data("workflow_state", {"phase": "active"})
                await activation.queue_instruction("activation-owned instruction")
                activation.subscribe(EventType.FS_FILE_CONTENT)
                return True

            async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult | None:
                return None

            async def on_tool(self) -> None:
                return None

        task_register(ActivationOnlyTask)
        task_manager = TaskManager(session=Mock(template_cache=Mock(), work=nullcontext))

        await task_manager.start_project_tasks(_session("alpha"))

        task = task_manager.get_task_by_type(ActivationOnlyTask)
        assert task is not None
        assert task.activation is not None
        assert task_manager.get_cached_data("workflow_state") == {"phase": "active"}
        assert [instruction.content for instruction in task_manager._pending_instructions] == [
            "activation-owned instruction"
        ]
        assert task_manager.get_subscription_count() == 1

    @pytest.mark.anyio
    async def test_registered_task_receives_its_activation_explicitly(self) -> None:
        """Runtime construction gives project tasks their explicit activation."""
        from mcp_guide.decorators import task_register

        task_register(_InjectedManagerProjectTask)
        task_manager = TaskManager()

        await task_manager.restart_project_tasks(_session("alpha"))
        task = task_manager.get_task_by_type(_InjectedManagerProjectTask)

        assert task is not None
        assert task.constructed_with is not None
        assert task.constructed_with.session.name == "alpha"

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
        update = Mock()
        update.changes.resolved_flags = {"command"}
        await task_manager.on_configuration_changed(session, update)
        second = task_manager.get_task_by_type(_ProjectTask)

        assert first is not second
        assert _ProjectTask.started_for == ["alpha", "alpha"]
        assert _ProjectTask.stopped_for == ["alpha"]
        assert task_manager.get_subscription_count() == 1

    @pytest.mark.anyio
    async def test_flag_reconciliation_retains_tasks_unrelated_to_the_changed_flag(self) -> None:
        """Declared task inputs prevent an unrelated flag from restarting a task."""
        from mcp_guide.decorators import task_register

        class WorkflowTask(_ProjectTask):
            configuration_flags = frozenset({"workflow"})

        class OpenSpecTask(_ProjectTask):
            configuration_flags = frozenset({"openspec"})

        task_register(WorkflowTask)
        task_register(OpenSpecTask)
        task_manager = TaskManager()
        session = _session("alpha")
        await task_manager.start_project_tasks(session)
        workflow = task_manager.get_task_by_type(WorkflowTask)
        openspec = task_manager.get_task_by_type(OpenSpecTask)

        await task_manager.reconcile_project_tasks(session, frozenset({"workflow"}))

        assert task_manager.get_task_by_type(WorkflowTask) is not workflow
        assert task_manager.get_task_by_type(OpenSpecTask) is openspec

    @pytest.mark.anyio
    async def test_flag_reconciliation_clears_cache_owned_by_replaced_task(self) -> None:
        """A replaced task cannot retain cache data for its prior configuration."""
        from mcp_guide.decorators import task_register

        class FlaggedTask(_ProjectTask):
            configuration_flags = frozenset({"workflow"})

            async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult | None:
                assert self.activation is not None
                self.activation.set_cached_data("flagged-task-state", {"active": True})
                return EventResult(result=True)

        task_register(FlaggedTask)
        task_manager = TaskManager()
        session = _session("alpha")
        await task_manager.start_project_tasks(session)
        await task_manager.dispatch_event(EventType.FS_FILE_CONTENT, {})

        assert task_manager.get_cached_data("flagged-task-state") == {"active": True}

        await task_manager.reconcile_project_tasks(session, frozenset({"workflow"}))

        assert task_manager.get_cached_data("flagged-task-state") is None

    @pytest.mark.anyio
    async def test_flag_reconciliation_clears_state_when_called_from_task_dispatch(self) -> None:
        """Reconciliation clears task state even while its prior dispatch is still active."""
        from mcp_guide.decorators import task_register

        class FlaggedTask(_ProjectTask):
            configuration_flags = frozenset({"workflow"})

            async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult | None:
                assert self.activation is not None
                self.activation.set_cached_data("flagged-task-state", {"active": True})
                await task_manager.reconcile_project_tasks(self.activation.session, frozenset({"workflow"}))
                return EventResult(result=True)

        task_register(FlaggedTask)
        task_manager = TaskManager()
        session = _session("alpha")
        await task_manager.start_project_tasks(session)

        await task_manager.dispatch_event(EventType.FS_FILE_CONTENT, {})

        assert task_manager.get_cached_data("flagged-task-state") is None

    @pytest.mark.anyio
    async def test_flag_reconciliation_drops_instruction_owned_by_replaced_task(self) -> None:
        """A replaced task cannot deliver an instruction after its flag changes."""
        from mcp_guide.decorators import task_register

        class FlaggedTask(_ProjectTask):
            configuration_flags = frozenset({"workflow"})

            async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult | None:
                assert self.activation is not None
                self.instruction_id = await self.activation.queue_instruction_with_ack("old task instruction")
                return EventResult(result=True)

        task_register(FlaggedTask)
        task_manager = TaskManager()
        session = _session("alpha")
        await task_manager.start_project_tasks(session)
        await task_manager.dispatch_event(EventType.FS_FILE_CONTENT, {})
        task = task_manager.get_task_by_type(FlaggedTask)

        assert task is not None
        assert task.instruction_id in task_manager._tracked_instructions

        await task_manager.reconcile_project_tasks(session, frozenset({"workflow"}))
        result = await task_manager.process_result(Result.ok("unchanged"))

        assert task.instruction_id not in task_manager._tracked_instructions
        assert result.additional_agent_instructions is None

    @pytest.mark.anyio
    async def test_flag_reconciliation_retains_state_owned_by_unaffected_task(self) -> None:
        """A task unaffected by a flag change retains its valid state."""
        from mcp_guide.decorators import task_register

        class ChangedTask(_ProjectTask):
            configuration_flags = frozenset({"workflow"})

        class RetainedTask(_ProjectTask):
            configuration_flags = frozenset({"openspec"})

            async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult | None:
                assert self.activation is not None
                self.activation.set_cached_data("retained-task-state", {"active": True})
                await self.activation.queue_instruction_with_ack("retained task instruction")
                return EventResult(result=True)

        task_register(ChangedTask)
        task_register(RetainedTask)
        task_manager = TaskManager()
        session = _session("alpha")
        await task_manager.start_project_tasks(session)
        await task_manager.dispatch_event(EventType.FS_FILE_CONTENT, {})

        await task_manager.reconcile_project_tasks(session, frozenset({"workflow"}))
        result = await task_manager.process_result(Result.ok("unchanged"))

        assert task_manager.get_cached_data("retained-task-state") == {"active": True}
        assert result.additional_agent_instructions == "retained task instruction"

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
    async def test_restart_serialises_a_waiting_stop_before_the_next_start(self) -> None:
        """A later restart waits for retirement and leaves one replacement active."""
        from mcp_guide.decorators import task_register

        task_register(_BlockingStopProjectTask)
        task_manager = TaskManager()
        await task_manager.restart_project_tasks(_session("alpha"))
        _BlockingStopProjectTask.stop_started = asyncio.Event()
        _BlockingStopProjectTask.allow_stop = asyncio.Event()

        first_restart = asyncio.create_task(task_manager.restart_project_tasks(_session("beta")))
        await _BlockingStopProjectTask.stop_started.wait()
        second_restart = asyncio.create_task(task_manager.restart_project_tasks(_session("gamma")))
        await asyncio.sleep(0)
        assert not second_restart.done()
        _BlockingStopProjectTask.allow_stop.set()
        await first_restart
        await second_restart

        active = task_manager.get_task_by_type(_BlockingStopProjectTask)
        assert active is not None
        assert active.session_name == "gamma"
        assert task_manager.get_subscription_count() == 1

    @pytest.mark.anyio
    async def test_restart_clears_project_scoped_cache_entries(self) -> None:
        """Lifecycle restart clears volatile cache values from the previous project."""
        task_manager = TaskManager(session=Mock(template_cache=Mock(), work=nullcontext))
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
    async def test_restart_clears_command_discovery_cache(self) -> None:
        """A restart cannot retain commands filtered for an earlier flag state."""
        task_manager = TaskManager()
        task_manager.command_cache["/client/_commands"] = (0.0, [{"name": "openspec/list"}])

        await task_manager.restart_project_tasks(_session("alpha"))

        assert task_manager.command_cache == {}

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
    async def test_retirement_preserves_identical_unowned_instruction(self) -> None:
        """Retiring task-owned text does not discard an identical unowned entry."""
        task_manager = TaskManager()
        task = _ProjectTask()
        activation = TaskActivation(task_manager, task, _session("alpha"))

        await task_manager.queue_instruction("same instruction")
        await activation.queue_instruction_with_ack("same instruction")
        activation.retire()

        assert [instruction.content for instruction in task_manager._pending_instructions] == ["same instruction"]
        result = await task_manager.process_result(Result.ok())
        assert result.additional_agent_instructions == "same instruction"

    @pytest.mark.anyio
    async def test_unowned_instruction_does_not_dispatch_identical_activation_callback(self) -> None:
        """A delivery callback belongs to its own queued instruction entry."""
        task_manager = TaskManager()
        task = _ProjectTask()
        activation = TaskActivation(task_manager, task, _session("alpha"))
        dispatched: list[bool] = []

        async def on_dispatch() -> None:
            dispatched.append(True)

        await task_manager.queue_instruction("same instruction")
        await activation.queue_instruction_with_ack("same instruction", on_dispatch=on_dispatch)

        first = await task_manager.process_result(Result.ok())

        assert first.additional_agent_instructions == "same instruction"
        assert dispatched == []

        second = await task_manager.process_result(Result.ok())

        assert second.additional_agent_instructions == "same instruction"
        assert dispatched == [True]

    @pytest.mark.anyio
    async def test_stale_event_handler_cannot_restore_project_scoped_state(self) -> None:
        """An event started before a restart cannot write into its replacement state."""
        from mcp_guide.decorators import task_register

        task_manager = TaskManager(session=Mock(template_cache=Mock(), work=nullcontext))
        handler_started = asyncio.Event()
        release_handler = asyncio.Event()

        class BlockingHandler(_ProjectTask):
            async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult | None:
                handler_started.set()
                await release_handler.wait()
                assert self.activation is not None
                await self.activation.queue_instruction("instruction from old root")
                self.activation.set_cached_data("workflow_state", {"phase": "old"})
                return EventResult(result=True, message="old-root result")

        task_register(BlockingHandler)
        await task_manager.start_project_tasks(_session("old"))
        dispatching = asyncio.create_task(task_manager.dispatch_event(EventType.FS_FILE_CONTENT, {}))
        await handler_started.wait()
        await task_manager.restart_project_tasks(_session("alpha"))
        release_handler.set()
        results = await dispatching

        assert task_manager._pending_instructions == []
        assert task_manager.get_cached_data("workflow_state") is None
        assert results == []

    @pytest.mark.anyio
    async def test_stale_timer_handler_cannot_restore_project_scoped_state(self) -> None:
        """A timer callback resumed after replacement cannot restore old task state."""
        from mcp_guide.decorators import task_register

        task_manager = TaskManager(session=Mock(template_cache=Mock(), work=nullcontext))
        timer_started = asyncio.Event()
        release_timer = asyncio.Event()

        class BlockingTimerTask(_ProjectTask):
            async def start(self, activation: TaskActivation) -> bool:
                self.activation = activation
                self.session_name = activation.session.name
                activation.subscribe(EventType.TIMER)
                return True

            async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult | None:
                if self.session_name != "old":
                    return None
                timer_started.set()
                await release_timer.wait()
                assert self.activation is not None
                await self.activation.queue_instruction("instruction from old timer")
                self.activation.set_cached_data("workflow_state", {"phase": "old"})
                return EventResult(result=True, message="old timer result")

        task_register(BlockingTimerTask)
        await task_manager.start_project_tasks(_session("old"))
        dispatching = asyncio.create_task(task_manager.dispatch_event(EventType.TIMER, {}))
        await timer_started.wait()
        await task_manager.restart_project_tasks(_session("new"))
        release_timer.set()
        results = await dispatching

        assert task_manager._pending_instructions == []
        assert task_manager.get_cached_data("workflow_state") is None
        assert results == []

    @pytest.mark.anyio
    async def test_stopped_project_task_cannot_restore_retired_state(self) -> None:
        """A stop callback cannot queue state after its task has been detached."""
        from mcp_guide.decorators import task_register

        class StateWritingStopTask(_ProjectTask):
            async def stop(self) -> None:
                assert self.activation is not None
                await self.activation.queue_instruction("instruction from retired task")
                self.activation.set_cached_data("workflow_state", {"phase": "retired"})

        task_register(StateWritingStopTask)
        task_manager = TaskManager(session=Mock(template_cache=Mock(), work=nullcontext))

        await task_manager.restart_project_tasks(_session("alpha"))
        await task_manager.restart_project_tasks(_session("beta"))

        assert task_manager._pending_instructions == []
        assert task_manager.get_cached_data("workflow_state") is None

    @pytest.mark.anyio
    async def test_tool_callback_state_is_owned_and_retired_with_its_task(self) -> None:
        """State emitted by on_tool is removed when that project task is replaced."""
        from mcp_guide.decorators import task_register

        class ToolStateTask(_ProjectTask):
            async def on_tool(self) -> None:
                assert self.session_name is not None
                assert self.activation is not None
                self.activation.set_cached_data("workflow_state", {"phase": self.session_name})
                await self.activation.queue_instruction(f"instruction for {self.session_name}")

        task_register(ToolStateTask)
        task_manager = TaskManager(session=Mock(template_cache=Mock(), work=nullcontext))

        await task_manager.restart_project_tasks(_session("alpha"))
        await task_manager.on_tool()
        active_tasks = await task_manager._detach_project_tasks(
            task_classes=frozenset({ToolStateTask}), clear_state=False
        )
        await task_manager._stop_project_tasks(active_tasks)

        assert task_manager._pending_instructions == []
        assert task_manager.get_cached_data("workflow_state") is None

    @pytest.mark.anyio
    async def test_stale_tool_callback_cannot_restore_project_state(self) -> None:
        """An on_tool callback started before replacement cannot write afterward."""
        from mcp_guide.decorators import task_register

        callback_started = asyncio.Event()
        release_callback = asyncio.Event()

        class BlockingToolTask(_ProjectTask):
            async def on_tool(self) -> None:
                callback_started.set()
                await release_callback.wait()
                assert self.activation is not None
                await self.activation.queue_instruction("instruction from old tool callback")
                self.activation.set_cached_data("workflow_state", {"phase": "old"})

        task_register(BlockingToolTask)
        task_manager = TaskManager(session=Mock(template_cache=Mock(), work=nullcontext))

        await task_manager.restart_project_tasks(_session("alpha"))
        tool_callback = asyncio.create_task(task_manager.on_tool())
        await callback_started.wait()
        await task_manager.restart_project_tasks(_session("beta"))
        release_callback.set()
        await tool_callback

        assert task_manager._pending_instructions == []
        assert task_manager.get_cached_data("workflow_state") is None

    @pytest.mark.anyio
    async def test_stale_project_task_start_cannot_restore_replaced_state(self) -> None:
        """A start callback resumed after replacement cannot write old state."""
        from mcp_guide.decorators import task_register

        start_started = asyncio.Event()
        release_start = asyncio.Event()

        class DelayedStartTask(_ProjectTask):
            async def start(self, activation: TaskActivation) -> bool:
                self.activation = activation
                self.session_name = activation.session.name
                if activation.session.name == "old":
                    start_started.set()
                    await release_start.wait()
                    await activation.queue_instruction("instruction from stale start")
                    activation.set_cached_data("workflow_state", {"phase": "old"})
                return False

        task_register(DelayedStartTask)
        task_manager = TaskManager(session=Mock(template_cache=Mock(), work=nullcontext))

        starting = asyncio.create_task(task_manager.start_project_tasks(_session("old")))
        await start_started.wait()
        restarting = asyncio.create_task(task_manager.restart_project_tasks(_session("new")))
        await asyncio.sleep(0)
        assert not restarting.done()
        release_start.set()
        await starting
        await restarting

        assert task_manager._pending_instructions == []
        assert task_manager.get_cached_data("workflow_state") is None

    @pytest.mark.anyio
    async def test_declined_project_task_start_clears_its_owned_state(self) -> None:
        """A task that declines activation cannot leave queued startup state behind."""
        from mcp_guide.decorators import task_register

        class DeclinedStartTask(_ProjectTask):
            async def start(self, activation: TaskActivation) -> bool:
                self.activation = activation
                self.session_name = activation.session.name
                await activation.queue_instruction("instruction from declined start")
                activation.set_cached_data("workflow_state", {"phase": "declined"})
                return False

        task_register(DeclinedStartTask)
        task_manager = TaskManager(session=Mock(template_cache=Mock(), work=nullcontext))

        await task_manager.start_project_tasks(_session("alpha"))

        assert task_manager._pending_instructions == []
        assert task_manager.get_cached_data("workflow_state") is None

    @pytest.mark.anyio
    async def test_stale_instruction_dispatch_callback_cannot_restore_task_state(self) -> None:
        """A delivery callback resumed after replacement cannot write old state."""
        from mcp_guide.decorators import task_register

        callback_started = asyncio.Event()
        release_callback = asyncio.Event()

        class DispatchCallbackTask(_ProjectTask):
            configuration_flags = frozenset({"workflow"})

            async def start(self, activation: TaskActivation) -> bool:
                self.activation = activation
                self.session_name = activation.session.name

                async def on_dispatch() -> None:
                    callback_started.set()
                    await release_callback.wait()
                    await activation.queue_instruction("instruction from stale dispatch callback")
                    activation.set_cached_data("workflow_state", {"phase": "old"})

                await activation.queue_instruction_with_ack("dispatch callback instruction", on_dispatch=on_dispatch)
                activation.subscribe(EventType.FS_FILE_CONTENT)
                return True

        task_register(DispatchCallbackTask)
        task_manager = TaskManager(session=Mock(template_cache=Mock(), work=nullcontext))

        await task_manager.start_project_tasks(_session("old"))
        delivering = asyncio.create_task(task_manager.process_result(Result.ok("unchanged")))
        await callback_started.wait()
        await task_manager.reconcile_project_tasks(_session("new"), frozenset({"workflow"}))
        release_callback.set()
        await delivering

        assert "instruction from stale dispatch callback" not in {
            instruction.content for instruction in task_manager._pending_instructions
        }
        assert task_manager.get_cached_data("workflow_state") is None

    @pytest.mark.anyio
    async def test_retired_task_cannot_receive_a_new_dispatch(self) -> None:
        """Retirement removes activation-owned subscriptions before another event."""
        from mcp_guide.decorators import task_register

        task_manager = TaskManager(session=Mock(template_cache=Mock(), work=nullcontext))

        class OldTask(_ProjectTask):
            async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> EventResult | None:
                assert self.activation is not None
                await self.activation.queue_instruction("OLD ROOT")
                self.activation.set_cached_data("workflow_state", {"phase": "old"})
                return EventResult(result=True, message="old-root result")

        task_register(OldTask)
        await task_manager.start_project_tasks(_session("old"))

        active_tasks = await task_manager._detach_project_tasks()
        results = await task_manager.dispatch_event(EventType.FS_FILE_CONTENT, {})
        await task_manager._stop_project_tasks(active_tasks)

        assert task_manager._pending_instructions == []
        assert task_manager.get_cached_data("workflow_state") is None
        assert results == []

    def test_stale_command_discovery_cannot_repopulate_the_cache(self) -> None:
        """A discovery result computed before invalidation is discarded."""
        task_manager = TaskManager()
        generation = task_manager.command_cache_generation

        task_manager.clear_command_cache()

        assert not task_manager.cache_commands("/client/_commands", 0.0, [{"name": "old"}], generation)
        assert task_manager.command_cache == {}

    @pytest.mark.anyio
    async def test_cleanup_clears_command_discovery_cache(self) -> None:
        """Terminal cleanup releases all project-derived command listings."""
        task_manager = TaskManager()
        task_manager.command_cache["/client/_commands"] = (0.0, [{"name": "openspec/list"}])

        await task_manager.cleanup()

        assert task_manager.command_cache == {}

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
        first_activation = TaskActivation(task_manager, first, _session("first"))
        second_activation = TaskActivation(task_manager, second, _session("second"))
        await first.start(first_activation)
        await second.start(second_activation)
        task_manager._active_project_tasks = {_ProjectTask: first, _InactiveProjectTask: second}
        task_manager._project_task_activations = {
            _ProjectTask: first_activation,
            _InactiveProjectTask: second_activation,
        }
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
        assert task_manager.get_subscription_count() == 0
        assert _CancelledStartProjectTask.stopped_for == ["alpha"]

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
    async def test_selective_timer_start_failure_retains_unaffected_project_tasks(self, monkeypatch) -> None:
        """A failed replacement must not discard the retained task registry."""
        from mcp_guide.decorators import task_register

        class WorkflowTask(_ProjectTask):
            configuration_flags = frozenset({"workflow"})

        class OpenSpecTask(_ProjectTask):
            configuration_flags = frozenset({"openspec"})

        task_register(WorkflowTask)
        task_register(OpenSpecTask)
        task_manager = TaskManager()
        session = _session("alpha")
        await task_manager.start_project_tasks(session)
        openspec = task_manager.get_task_by_type(OpenSpecTask)

        async def fail_timer_start() -> None:
            raise RuntimeError("timer startup failed")

        monkeypatch.setattr(task_manager, "start", fail_timer_start)

        with pytest.raises(RuntimeError, match="timer startup failed"):
            await task_manager.reconcile_project_tasks(session, frozenset({"workflow"}))

        assert task_manager.get_task_by_type(OpenSpecTask) is openspec
        assert task_manager._active_project_tasks[OpenSpecTask] is openspec
        assert task_manager.get_subscription_count() == 1

    @pytest.mark.anyio
    async def test_project_entry_removal_stops_project_scoped_tasks(self) -> None:
        """Removing the active project must release its task subscriptions."""
        from mcp_guide.decorators import task_register

        task_register(_ProjectTask)
        task_manager = TaskManager()
        session = _session("alpha")
        await task_manager.start_project_tasks(session)
        update = Mock()
        update.current_project = None
        update.changes.project_entry_changed = True
        update.changes.resolved_flags = frozenset()
        update.changes.project_flags = frozenset()

        await task_manager.on_configuration_changed(session, update)

        assert task_manager.get_subscription_count() == 0
        assert task_manager._active_project_tasks == {}

    @pytest.mark.anyio
    async def test_project_entry_recreation_restarts_project_scoped_tasks(self) -> None:
        """Recreating the active project starts fresh project-scoped tasks."""
        from mcp_guide.decorators import task_register

        task_register(_ProjectTask)
        task_manager = TaskManager()
        session = _session("alpha")
        update = Mock()
        update.current_project = object()
        update.changes.project_entry_changed = True
        update.changes.resolved_flags = frozenset()
        update.changes.project_flags = frozenset()

        await task_manager.on_configuration_changed(session, update)

        task = task_manager.get_task_by_type(_ProjectTask)
        assert task is not None
        assert task.session_name == "alpha"

    @pytest.mark.anyio
    async def test_cleanup_finishes_after_stop_cancellation(self) -> None:
        """Cancellation from one stop hook does not skip later task cleanup."""
        task_manager = TaskManager()
        cancelled = _CancelledStopProjectTask()
        remaining = _ProjectTask()
        await cancelled.start(TaskActivation(task_manager, cancelled, _session("cancelled")))
        await remaining.start(TaskActivation(task_manager, remaining, _session("remaining")))

        with pytest.raises(asyncio.CancelledError):
            await task_manager._cleanup_started_project_tasks([cancelled, remaining])

        assert _ProjectTask.stopped_for == ["remaining"]
        assert task_manager.get_subscription_count() == 0

    @pytest.mark.anyio
    @pytest.mark.parametrize("failing_class", [_FailingStopProjectTask, _CancelledStopProjectTask])
    async def test_disposal_reports_failure_after_attempting_remaining_tasks(self, failing_class) -> None:
        """Disposal must not report success when a task's stop hook failed."""
        task_manager = TaskManager()
        failing, remaining = failing_class(), _ProjectTask()
        failing_activation = TaskActivation(task_manager, failing, _session("failing"))
        remaining_activation = TaskActivation(task_manager, remaining, _session("remaining"))
        await failing.start(failing_activation)
        await remaining.start(remaining_activation)
        task_manager._active_project_tasks = {failing_class: failing, _ProjectTask: remaining}
        task_manager._project_task_activations = {
            failing_class: failing_activation,
            _ProjectTask: remaining_activation,
        }

        with pytest.raises((RuntimeError, asyncio.CancelledError)):
            await task_manager.cleanup()

        assert "remaining" in _ProjectTask.stopped_for
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
        assert "Error cleaning up failed project-scoped task" in caplog.text
