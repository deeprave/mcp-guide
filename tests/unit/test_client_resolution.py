"""Client expansion requires verified sharing; dispatch starts response timing."""

import asyncio
from pathlib import Path

import pytest

from mcp_guide.lazy_path import LazyPath
from mcp_guide.result import Result
from mcp_guide.task_manager.manager import TaskManager


@pytest.mark.anyio
@pytest.mark.parametrize("shared", [None, False, True])
@pytest.mark.parametrize("path", ["relative-project", "../project", "$GUIDE_RELATIVE_ROOT/project"])
async def test_initial_binding_rejects_relative_paths(runtime, monkeypatch, shared, path):
    from tests.helpers import create_unbound_test_session

    monkeypatch.setattr(LazyPath, "client_filesystem_shared", shared)
    monkeypatch.setenv("GUIDE_RELATIVE_ROOT", "relative")
    session = create_unbound_test_session(runtime)
    with pytest.raises(ValueError, match="absolute client path"):
        await session.bind_project_path(path)
    assert session.bound_root_path is None


@pytest.mark.anyio
@pytest.mark.parametrize("shared", [None, False, True])
async def test_initial_binding_normalises_absolute_parent_components(runtime, tmp_path, monkeypatch, shared):
    from tests.helpers import create_unbound_test_session

    monkeypatch.setattr(LazyPath, "client_filesystem_shared", shared)
    session = create_unbound_test_session(runtime)
    await session.bind_project_path(tmp_path / "intermediate" / ".." / "project")
    assert session.bound_root_path == tmp_path / "project"
    assert session.project_name == "project"
    await session.cleanup()


@pytest.mark.parametrize("shared", [None, False])
@pytest.mark.parametrize(
    "path", ["../project", "~/project", "~root/project", "$ROOT/project", "/client/${ROOT}/project"]
)
def test_unverified_client_paths_reject_shorthand(monkeypatch, shared, path):
    monkeypatch.setattr(LazyPath, "client_filesystem_shared", shared, raising=False)
    with pytest.raises(ValueError, match="absolute client path"):
        LazyPath(path).client_resolve()


@pytest.mark.parametrize("shared", [None, False, True])
def test_client_resolution_only_follows_shared_symlinks(tmp_path, monkeypatch, shared):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target)
    monkeypatch.setattr(LazyPath, "client_filesystem_shared", shared, raising=False)
    assert LazyPath(link / "child").client_resolve() == (target if shared else link) / "child"


def test_verified_client_paths_expand_user_and_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(LazyPath, "client_filesystem_shared", True, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("GUIDE_TEST_ROOT", str(tmp_path))
    assert LazyPath("~/project").client_resolve() == tmp_path / "project"
    assert LazyPath("$GUIDE_TEST_ROOT/project").client_resolve() == tmp_path / "project"
    assert LazyPath("~root/project").client_resolve() == Path("~root/project").expanduser().resolve()


@pytest.mark.anyio
async def test_instruction_dispatch_notification_waits_behind_queue():
    manager = TaskManager()
    dispatched = []

    async def on_dispatch():
        dispatched.append("probe")

    await manager.queue_instruction("earlier")
    instruction_id = await manager.queue_instruction_with_ack("probe", on_dispatch=on_dispatch)
    manager._tracked_instructions[instruction_id].last_sent_at = 0
    await manager.retry_unacknowledged()
    assert dispatched == []
    first = await manager.process_result(Result.ok())
    assert first.additional_agent_instructions == "earlier"
    assert dispatched == []
    second = await manager.process_result(Result.ok())
    assert second.additional_agent_instructions == "probe"
    assert dispatched == ["probe"]
    await manager.acknowledge_instruction(instruction_id)
    await manager.process_result(Result.ok())
    assert dispatched == ["probe"]


@pytest.mark.anyio
async def test_only_one_probe_is_pending_and_disposal_removes_queued_probe(runtime, tmp_path, monkeypatch):
    from tests.helpers import create_unbound_test_session

    from mcp_guide import decorators
    from mcp_guide.tasks.filesystem_probe import FilesystemProbeTask

    monkeypatch.setattr(decorators, "_registered_task_classes", [FilesystemProbeTask])
    monkeypatch.setattr(FilesystemProbeTask, "_pending", False)
    first = create_unbound_test_session(runtime)
    second = create_unbound_test_session(runtime)
    await first.prepare_binding("first", tmp_path)
    await second.prepare_binding("second", tmp_path)
    await first.task_manager.start_project_tasks(first)
    await second.task_manager.start_project_tasks(second)
    assert len(list(tmp_path.glob(".mcp-guide-fs-probe-*"))) == 1
    assert second.task_manager.is_queue_empty()
    await first.cleanup()
    assert LazyPath.client_filesystem_shared is False
    assert not FilesystemProbeTask._pending
    assert not list(tmp_path.glob(".mcp-guide-fs-probe-*"))
    assert first.task_manager.is_queue_empty()
    assert not first.task_manager._tracked_instructions
    assert not first.task_manager._subscriptions
    await second.cleanup()


@pytest.mark.anyio
@pytest.mark.parametrize("parent", ["missing", "embedded\0null"], ids=["missing-directory", "invalid-path"])
async def test_probe_creation_failure_leaves_binding_usable(runtime, tmp_path, monkeypatch, parent):
    from tests.helpers import create_unbound_test_session

    from mcp_guide import decorators
    from mcp_guide.tasks.filesystem_probe import FilesystemProbeTask

    monkeypatch.setattr(decorators, "_registered_task_classes", [FilesystemProbeTask])
    monkeypatch.setattr(FilesystemProbeTask, "_pending", False)
    session = create_unbound_test_session(runtime)
    root = tmp_path / parent / "project"
    await session.bind_project_path(root)
    await session.task_manager.start_project_tasks(session)
    assert session.bound_root_path == root
    assert LazyPath.client_filesystem_shared is False
    assert not FilesystemProbeTask._pending
    assert session.task_manager.is_queue_empty()
    assert not session.task_manager._tracked_instructions
    assert not any(isinstance(s.subscriber, FilesystemProbeTask) for s in session.task_manager._subscriptions)
    await session.cleanup()


@pytest.mark.anyio
async def test_verification_does_not_change_an_already_bound_lexical_identity(runtime, tmp_path, monkeypatch):
    from tests.helpers import create_unbound_test_session, request_context_for

    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target)
    session = create_unbound_test_session(runtime)
    await session.bind_project_path(link)
    context = await request_context_for(session)
    identity = context.root
    monkeypatch.setattr(LazyPath, "client_filesystem_shared", True)
    assert context.root == identity
    assert context.root.path == str(link)
    await session.cleanup()


@pytest.mark.anyio
@pytest.mark.parametrize("matches", [True, False])
async def test_probe_consumes_only_its_response_and_cleans_up(runtime, tmp_path, monkeypatch, matches):
    from tests.helpers import create_unbound_test_session

    from mcp_guide.task_manager import EventType
    from mcp_guide.tasks.filesystem_probe import FilesystemProbeTask

    monkeypatch.setattr(LazyPath, "client_filesystem_shared", None)
    monkeypatch.setattr(FilesystemProbeTask, "_pending", False)
    session = create_unbound_test_session(runtime)
    await session.prepare_binding(tmp_path.name, tmp_path)
    manager = session.task_manager
    received = []

    class Receiver:
        def get_name(self):
            return "Receiver"

        async def handle_event(self, event_type, data):
            received.append(data["path"])

    receiver = Receiver()
    manager.subscribe(receiver, EventType.FS_FILE_CONTENT)
    task = FilesystemProbeTask(manager)
    try:
        assert await task.start(manager, session)
        (probe,) = tmp_path.glob(".mcp-guide-fs-probe-*")
        challenge = probe.read_text()
        response = await manager.process_result(Result.ok())
        assert str(probe) in response.additional_agent_instructions
        assert challenge not in response.additional_agent_instructions
        await manager.dispatch_event(EventType.FS_FILE_CONTENT, {"path": str(probe) + "-other", "content": challenge})
        assert LazyPath.client_filesystem_shared is None
        received.clear()
        results = await manager.dispatch_event(
            EventType.FS_FILE_CONTENT, {"path": str(probe), "content": challenge if matches else "wrong"}
        )
        assert len(results) == 1
        assert received == []
        assert LazyPath.client_filesystem_shared is matches
        assert not probe.exists()
        assert not manager._tracked_instructions
        assert all(s.subscriber is not task for s in manager._subscriptions)
    finally:
        await task.stop(manager)


@pytest.mark.anyio
async def test_probe_timeout_starts_at_dispatch_not_queue(runtime, tmp_path, monkeypatch):
    from tests.helpers import create_unbound_test_session

    from mcp_guide.tasks import filesystem_probe

    monkeypatch.setattr(LazyPath, "client_filesystem_shared", None)
    monkeypatch.setattr(filesystem_probe.FilesystemProbeTask, "_pending", False)
    monkeypatch.setattr(filesystem_probe, "PROBE_TIMEOUT_SECONDS", 0.02)
    session = create_unbound_test_session(runtime)
    await session.prepare_binding(tmp_path.name, tmp_path)
    manager = session.task_manager
    task = filesystem_probe.FilesystemProbeTask(manager)
    try:
        await manager.queue_instruction("earlier")
        assert await task.start(manager, session)
        await asyncio.sleep(0.04)
        assert LazyPath.client_filesystem_shared is None
        assert list(tmp_path.glob(".mcp-guide-fs-probe-*"))
        await manager.process_result(Result.ok())
        await asyncio.sleep(0.04)
        assert LazyPath.client_filesystem_shared is None
        await manager.process_result(Result.ok())
        await asyncio.sleep(0.04)
        assert LazyPath.client_filesystem_shared is False
        assert not list(tmp_path.glob(".mcp-guide-fs-probe-*"))
        assert manager.is_queue_empty()
        assert not manager._tracked_instructions
    finally:
        await task.stop(manager)


@pytest.mark.anyio
async def test_disabled_probe_does_not_create_or_queue(runtime, tmp_path, monkeypatch):
    from tests.helpers import create_unbound_test_session

    from mcp_guide.tasks.filesystem_probe import FilesystemProbeTask

    monkeypatch.setattr(LazyPath, "client_filesystem_shared", False)
    session = create_unbound_test_session(runtime)
    await session.prepare_binding(tmp_path.name, tmp_path)
    task = FilesystemProbeTask(session.task_manager)
    assert not await task.start(session.task_manager, session)
    assert not list(tmp_path.glob(".mcp-guide-fs-probe-*"))
    assert session.task_manager.is_queue_empty()


@pytest.mark.anyio
@pytest.mark.parametrize("transport", ["stdio", "http", "https"])
async def test_application_start_sets_probe_policy(tmp_path, monkeypatch, transport):
    from tests.helpers import create_unbound_test_session

    from mcp_guide import decorators
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application
    from mcp_guide.session import bind_session_project
    from mcp_guide.tasks.filesystem_probe import FilesystemProbeTask

    monkeypatch.setattr(LazyPath, "client_filesystem_shared", True)
    # Other task tests clear the import-time registry; model fresh startup explicitly.
    monkeypatch.setattr(decorators, "_registered_task_classes", [FilesystemProbeTask])
    monkeypatch.setattr(FilesystemProbeTask, "_pending", False)
    app = create_application(
        ServerConfig(configdir=str(tmp_path / "config"), docroot=str(tmp_path / "docs"), transport_mode=transport)
    )
    await app.runtime.start()
    try:
        assert LazyPath.client_filesystem_shared is (None if transport == "stdio" else False)
        root = tmp_path / "project"
        root.mkdir()
        session = create_unbound_test_session(app.runtime)
        await bind_session_project(session, root)
        assert bool(list(root.glob(".mcp-guide-fs-probe-*"))) is (transport == "stdio")
    finally:
        await app.runtime.stop()
    assert not list(tmp_path.glob("project/.mcp-guide-fs-probe-*"))


@pytest.mark.anyio
@pytest.mark.parametrize("shared", [None, False, True])
async def test_switch_enforces_verified_shorthand(runtime, tmp_path, monkeypatch, shared):
    from tests.helpers import create_unbound_test_session

    monkeypatch.setattr(LazyPath, "client_filesystem_shared", shared)
    session = create_unbound_test_session(runtime)
    await session.bind_project_path(tmp_path / "original")
    if shared:
        replacement = await session.switch_project(path="../replacement")
        assert replacement.bound_root_path == tmp_path / "replacement"
    else:
        with pytest.raises(ValueError, match="absolute client path"):
            await session.switch_project(path="../replacement")
        assert session.bound_root_path == tmp_path / "original"
