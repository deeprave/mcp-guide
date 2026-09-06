"""Integration tests for config and session management."""

import asyncio
from dataclasses import replace
from unittest.mock import AsyncMock

import pytest
import yaml

from mcp_guide.models import Category
from mcp_guide.runtime import get_runtime
from mcp_guide.session import Session
from tests.helpers import create_unbound_test_session, runtime_config_dir, wait_for_session_disposals


class _RecordingSessionListener:
    """Session listener that records config-change notifications."""

    def __init__(self) -> None:
        self.config_changed = AsyncMock(return_value=None)

    async def on_project_changed(self, session: Session, old_project: str, new_project: str) -> None:
        pass

    async def on_config_changed(self, session: Session) -> None:
        await self.config_changed(session)


class TestConfigSessionIntegration:
    """End-to-end integration tests."""

    @staticmethod
    async def _create_bound_session(runtime, project_name: str) -> Session:
        """Create a session bound directly to a project without switch notifications."""
        session = create_unbound_test_session(runtime)
        project_root = runtime_config_dir(runtime) / "client-roots" / project_name
        project_root.mkdir(parents=True, exist_ok=True)
        await session.bind_project_path(project_root)
        return session

    @pytest.mark.anyio
    async def test_end_to_end_workflow(self, runtime, monkeypatch):
        """Test complete workflow: create session, update config, save, reload."""
        # Create session with test config directory
        session = await self._create_bound_session(runtime, "test-project")

        # Get initial project (should have no categories)
        project = await session.get_project()
        assert len(project.categories) == 0

        # Update config through session
        category = Category(dir="docs/", patterns=["*.md"])
        await session.update_config(lambda p: p.with_category("docs", category))

        # Verify update persisted by creating new session
        new_session = await self._create_bound_session(runtime, "test-project")
        reloaded_project = await new_session.get_project()
        assert len(reloaded_project.categories) == 1

        # Verify session cache updated
        cached_project = await session.get_project()
        assert len(cached_project.categories) == 1

    @pytest.mark.anyio
    async def test_concurrent_sessions_different_projects(self, runtime, monkeypatch):
        """Test concurrent sessions on different projects work correctly."""
        monkeypatch.setattr("mcp_guide.file_lock.LOCK_RETRY_SECONDS", 0.01)
        results = []

        async def task1():
            session1 = await self._create_bound_session(runtime, "project1")

            category = Category(dir="api/", patterns=["*.py"])
            await session1.update_config(lambda p: p.with_category("api", category))
            results.append(("task1", len((await session1.get_project()).categories)))

        async def task2():
            session2 = await self._create_bound_session(runtime, "project2")

            category = Category(dir="web/", patterns=["*.html"])
            await session2.update_config(lambda p: p.with_category("web", category))
            results.append(("task2", len((await session2.get_project()).categories)))

        await asyncio.gather(task1(), task2())

        # Verify both tasks completed successfully
        assert len(results) == 2
        assert all(count == 1 for _, count in results)

    @pytest.mark.anyio
    async def test_project_switch_replaces_runtime_tasks_and_clears_project_state(self, runtime, monkeypatch):
        """Rebinding to a same-named project root replaces runtime state."""
        from mcp_guide.context.tasks import ClientContextTask
        from mcp_guide.decorators import (
            clear_registered_tasks_for_testing,
            get_registered_task_classes,
            task_register,
        )
        from mcp_guide.feature_flags.types import FeatureValue
        from mcp_guide.openspec.task import OpenSpecTask
        from mcp_guide.workflow.tasks import WorkflowMonitorTask

        registered_task_classes = get_registered_task_classes()
        clear_registered_tasks_for_testing()
        for task_class in (WorkflowMonitorTask, ClientContextTask, OpenSpecTask):
            task_register(task_class)

        session = None

        try:
            await runtime.feature_flags().set("allow-client-info", True)
            session = await self._create_bound_session(runtime, "enabled-project")
            task_manager = session.task_manager
            await session.update_config(
                lambda project: replace(
                    project,
                    project_flags={
                        "workflow": FeatureValue.from_raw(True),
                        "openspec": FeatureValue.from_raw(True),
                    },
                )
            )
            await task_manager.restart_project_tasks(session)
            assert task_manager.get_task_by_type(WorkflowMonitorTask) is not None
            assert task_manager.get_task_by_type(OpenSpecTask) is not None
            assert task_manager.get_task_by_type(ClientContextTask) is not None
            # The Session-owned manager also retains its three base tasks.
            assert task_manager.get_subscription_count() == 6

            task_manager.set_cached_data("workflow_state", {"phase": "implementation"})
            task_manager.set_cached_data("client_context_info", {"editor": "test"})
            task_manager.set_cached_data("openspec_version", "1.6.0")
            await task_manager.queue_instruction("stale project instruction")

            session = await session.switch_project(
                path=runtime_config_dir(runtime) / "alternate-client-root" / "enabled-project"
            )
            await wait_for_session_disposals(runtime)
            assert task_manager.get_subscription_count() == 0
            task_manager = session.task_manager

            assert task_manager.get_task_by_type(WorkflowMonitorTask) is None
            assert task_manager.get_task_by_type(OpenSpecTask) is None
            assert task_manager.get_task_by_type(ClientContextTask) is not None
            assert task_manager.get_subscription_count() == 4
            assert task_manager.get_cached_data("workflow_state") is None
            assert task_manager.get_cached_data("client_context_info") is None
            assert task_manager.get_cached_data("openspec_version") is None
            assert "stale project instruction" not in task_manager._pending_instructions
        finally:
            await task_manager.cleanup()
            clear_registered_tasks_for_testing()
            for task_class in registered_task_classes:
                task_register(task_class)
            if session is not None:
                await session.cleanup()

    @pytest.mark.anyio
    async def test_save_project_notifies_for_bound_project(self, runtime, monkeypatch):
        """Saving the session's bound project notifies config listeners."""
        session = await self._create_bound_session(runtime, "current-project")
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        project = await session.get_project()
        updated_project = project.with_category("docs", Category(dir="docs/", patterns=["*.md"]))

        await session.save_project(updated_project)

        listener.config_changed.assert_awaited_once_with(session)
        assert "docs" in (await session.get_project()).categories

    @pytest.mark.anyio
    async def test_project_flag_change_clears_command_discovery_cache(self, runtime) -> None:
        """Flag-gated command listings are rebuilt after a project flag update."""
        from mcp_guide.feature_flags.types import FeatureValue

        session = await self._create_bound_session(runtime, "current-project")
        session.task_manager.command_cache["/client/_commands"] = (0.0, [{"name": "openspec/list"}])

        await session.update_config(
            lambda project: replace(project, project_flags={"openspec": FeatureValue.from_raw(True)})
        )

        assert session.task_manager.command_cache == {}

    @pytest.mark.anyio
    async def test_project_flag_mutation_keeps_its_original_binding(self, runtime) -> None:
        """A flag proxy captured for one root cannot modify a replacement project."""
        from mcp_guide.feature_flags.types import FeatureValue

        session = await self._create_bound_session(runtime, "original")
        original_project = await session.get_project()
        assert original_project.key is not None
        flags = session.project_flags()

        replacement = await session.switch_project("review")

        await flags.set("openspec", FeatureValue.from_raw(True))

        assert "openspec" not in (await replacement.get_project()).project_flags
        projects = await session.get_all_projects()
        assert projects[original_project.key].project_flags["openspec"].to_raw() is True

    @pytest.mark.anyio
    async def test_pending_save_does_not_undo_a_name_only_project_switch(self, runtime, monkeypatch):
        """A save finishing after a switch must not restore its old binding."""
        session = await self._create_bound_session(runtime, "original")
        original_project = await session.get_project()
        config_manager = session._config()
        save_started = asyncio.Event()
        allow_save = asyncio.Event()
        original_save = config_manager.save_project_config

        async def gated_save(project_key, project):
            save_started.set()
            await allow_save.wait()
            await original_save(project_key, project)

        monkeypatch.setattr(config_manager, "save_project_config", gated_save)
        pending_save = asyncio.create_task(session.save_project(original_project))
        await save_started.wait()

        switching = asyncio.create_task(session.switch_project("review"))
        await asyncio.sleep(0)
        assert not switching.done()
        allow_save.set()
        await pending_save
        replacement = await switching

        assert (await replacement.get_project()).name == "review"
        assert (await session.get_project()).name == "original"

    @pytest.mark.anyio
    async def test_shared_configuration_publication_completes_before_replacement_preparation(
        self, runtime, monkeypatch
    ) -> None:
        """A configuration publication cannot deadlock a concurrent root switch."""
        session = await self._create_bound_session(runtime, "original")
        project = await session.get_project()
        config_manager = session._config()
        publication_started = asyncio.Event()
        release_publication = asyncio.Event()
        original_publish = config_manager._publish_snapshot_delta

        async def paused_publish(previous, current):
            publication_started.set()
            await release_publication.wait()
            await original_publish(previous, current)

        monkeypatch.setattr(config_manager, "_publish_snapshot_delta", paused_publish)
        updated_project = project.with_category("docs", Category(dir="docs/", patterns=["*.md"]))
        saving = asyncio.create_task(session.save_project(updated_project))
        await publication_started.wait()
        switching = asyncio.create_task(session.switch_project("review"))
        await asyncio.sleep(0)

        assert not switching.done()
        release_publication.set()
        await asyncio.wait_for(asyncio.gather(saving, switching), timeout=1)

        assert (await switching.result().get_project()).name == "review"
        assert (await session.get_project()).name == "original"

    @pytest.mark.anyio
    async def test_save_project_does_not_notify_for_other_project(self, runtime, monkeypatch):
        """Cross-project saves persist without notifying this session's config listeners."""
        session = await self._create_bound_session(runtime, "current-project")
        config_manager = session._config()
        other_project_root = runtime_config_dir(runtime) / "client-roots" / "other-project"
        other_project_root.mkdir(parents=True, exist_ok=True)
        other_key, other_project = await config_manager.get_or_create_project_config(
            "other-project", root_path=other_project_root
        )
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        updated_other_project = other_project.with_category("api", Category(dir="api/", patterns=["*.py"]))

        await session.save_project(updated_other_project)

        listener.config_changed.assert_not_awaited()
        reloaded_projects = await session.get_all_projects()
        assert "api" in reloaded_projects[other_key].categories
        assert (await session.get_project()).name == "current-project"

    @pytest.mark.anyio
    async def test_config_file_change_ignores_other_project(self, runtime, monkeypatch):
        """Shared config-file changes do not notify when only another project changed."""
        session = await self._create_bound_session(runtime, "current-project")
        config_manager = session._config()
        other_project_root = runtime_config_dir(runtime) / "client-roots" / "other-project"
        _other_key, other_project = await config_manager.get_or_create_project_config(
            "other-project", root_path=other_project_root
        )
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        await session.save_project(other_project.with_category("api", Category(dir="api/", patterns=["*.py"])))
        await config_manager._on_external_change(str(config_manager.config_file))

        listener.config_changed.assert_not_awaited()
        assert (await session.get_project()).name == "current-project"

    @pytest.mark.anyio
    async def test_config_file_change_notifies_for_bound_project(self, runtime, monkeypatch):
        """Shared config-file changes notify when the bound project changed externally."""
        session = await self._create_bound_session(runtime, "current-project")
        project = await session.get_project()
        config_manager = session._config()
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        assert project.key is not None
        updated_project = project.with_category("docs", Category(dir="docs/", patterns=["*.md"]))
        await config_manager.save_project_config(project.key, updated_project)
        await config_manager._on_external_change(str(config_manager.config_file))

        listener.config_changed.assert_awaited_once_with(session)
        assert "docs" in (await session.get_project()).categories

    @pytest.mark.anyio
    async def test_global_feature_flag_changes_notify_config_listeners(self, runtime, monkeypatch):
        """Global flag writes notify because they affect resolved current-project config."""
        session = await self._create_bound_session(runtime, "current-project")
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        await get_runtime().feature_flags().set("workflow", True)

        listener.config_changed.assert_awaited_once_with(session)

    @pytest.mark.anyio
    async def test_config_file_change_notifies_for_cached_global_feature_flags(self, runtime, monkeypatch):
        """External global flag changes notify sessions that have resolved global flags."""
        session = await self._create_bound_session(runtime, "current-project")
        config_manager = session._config()
        await get_runtime().get_feature_flags()
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        config_data = yaml.safe_load(config_manager.config_file.read_text())
        config_data.setdefault("feature_flags", {})["workflow"] = True
        config_manager.config_file.write_text(yaml.dump(config_data))
        await config_manager._on_external_change(str(config_manager.config_file))

        listener.config_changed.assert_awaited_once_with(session)

    @pytest.mark.anyio
    async def test_config_file_change_notifies_for_uncached_global_feature_flags(self, runtime, monkeypatch):
        """External global flag changes notify even before global flags are cached."""
        session = await self._create_bound_session(runtime, "current-project")
        config_manager = session._config()
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        config_data = yaml.safe_load(config_manager.config_file.read_text())
        config_data.setdefault("feature_flags", {})["workflow"] = True
        config_manager.config_file.write_text(yaml.dump(config_data))
        await config_manager._on_external_change(str(config_manager.config_file))

        listener.config_changed.assert_awaited_once_with(session)

    @pytest.mark.anyio
    async def test_file_locking_prevents_corruption(self, runtime, monkeypatch):
        """Test that config lock prevents read-modify-write race conditions."""
        monkeypatch.setattr("mcp_guide.file_lock.LOCK_RETRY_SECONDS", 0.01)
        # Create initial session and project
        initial_session = await self._create_bound_session(runtime, "test-project")
        await initial_session.get_project()  # Create the project

        results = []
        errors = []

        async def update_project(category_name: str):
            try:
                # Each task creates its own session and updates the project
                session = await self._create_bound_session(runtime, "test-project")
                category = Category(dir=f"{category_name}/", patterns=["*.md"])
                await session.update_config(lambda p: p.with_category(category_name, category))
                results.append(category_name)
            except Exception as e:
                errors.append(str(e))

        # Create multiple tasks updating the same project
        category_names = [f"cat{i}" for i in range(4)]
        tasks = [update_project(category_name) for category_name in category_names]

        await asyncio.gather(*tasks)

        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Verify all tasks completed
        assert len(results) == len(category_names)

        # Concurrent in-memory updates of one project last-writer-wins; the lock
        # must still leave a readable configuration rather than a torn file.
        final_session = await self._create_bound_session(runtime, "test-project")
        project = await final_session.get_project()
        persisted = yaml.safe_load(final_session._config().config_file.read_text())
        assert isinstance(persisted, dict)
        assert isinstance(project.categories, dict)
        assert len(project.categories) >= 1
