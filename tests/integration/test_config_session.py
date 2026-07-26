"""Integration tests for config and session management."""

import asyncio
from unittest.mock import AsyncMock

import pytest
import yaml

from mcp_guide.models import Category
from mcp_guide.session import Session, set_current_session


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
    async def _create_bound_session(project_name: str, config_dir: str) -> Session:
        """Create a session bound directly to a project without switch notifications."""
        session = Session(_config_dir_for_tests=config_dir)
        config_manager = session._get_config_manager(config_dir)
        _key, project = await config_manager.get_or_create_project_config(project_name)
        getattr(session, "_Session__delegate").bind(project)
        session._project_dirty = False
        return session

    @pytest.mark.anyio
    async def test_end_to_end_workflow(self, tmp_path, monkeypatch):
        """Test complete workflow: create session, update config, save, reload."""
        monkeypatch.setattr(Session, "_ensure_watcher_started", AsyncMock(return_value=None))
        monkeypatch.setattr(Session, "_notify_config_changed", AsyncMock(return_value=None))
        # Create session with test config directory
        session = await self._create_bound_session("test-project", str(tmp_path))
        set_current_session(session)

        # Get initial project (should have no categories)
        project = await session.get_project()
        assert len(project.categories) == 0

        # Update config through session
        category = Category(dir="docs/", patterns=["*.md"])
        await session.update_config(lambda p: p.with_category("docs", category))

        # Verify update persisted by creating new session
        new_session = await self._create_bound_session("test-project", str(tmp_path))
        reloaded_project = await new_session.get_project()
        assert len(reloaded_project.categories) == 1

        # Verify session cache updated
        cached_project = await session.get_project()
        assert len(cached_project.categories) == 1

    @pytest.mark.anyio
    async def test_concurrent_sessions_different_projects(self, tmp_path, monkeypatch):
        """Test concurrent sessions on different projects work correctly."""
        monkeypatch.setattr("mcp_guide.file_lock.LOCK_RETRY_SECONDS", 0.01)
        monkeypatch.setattr(Session, "_ensure_watcher_started", AsyncMock(return_value=None))
        monkeypatch.setattr(Session, "_notify_config_changed", AsyncMock(return_value=None))
        results = []
        config_dir = str(tmp_path)

        async def task1():
            session1 = await self._create_bound_session("project1", config_dir)

            category = Category(dir="api/", patterns=["*.py"])
            await session1.update_config(lambda p: p.with_category("api", category))
            results.append(("task1", len((await session1.get_project()).categories)))

        async def task2():
            session2 = await self._create_bound_session("project2", config_dir)

            category = Category(dir="web/", patterns=["*.html"])
            await session2.update_config(lambda p: p.with_category("web", category))
            results.append(("task2", len((await session2.get_project()).categories)))

        await asyncio.gather(task1(), task2())

        # Verify both tasks completed successfully
        assert len(results) == 2
        assert all(count == 1 for _, count in results)

    @pytest.mark.anyio
    async def test_save_project_notifies_for_bound_project(self, tmp_path, monkeypatch):
        """Saving the session's bound project notifies config listeners."""
        monkeypatch.setattr(Session, "_ensure_watcher_started", AsyncMock(return_value=None))
        session = await self._create_bound_session("current-project", str(tmp_path))
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        project = await session.get_project()
        updated_project = project.with_category("docs", Category(dir="docs/", patterns=["*.md"]))

        await session.save_project(updated_project)

        listener.config_changed.assert_awaited_once_with(session)
        assert "docs" in (await session.get_project()).categories

    @pytest.mark.anyio
    async def test_save_project_does_not_notify_for_other_project(self, tmp_path, monkeypatch):
        """Cross-project saves persist without notifying this session's config listeners."""
        monkeypatch.setattr(Session, "_ensure_watcher_started", AsyncMock(return_value=None))
        session = await self._create_bound_session("current-project", str(tmp_path))
        config_manager = session._get_config_manager(str(tmp_path))
        other_key, other_project = await config_manager.get_or_create_project_config("other-project")
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        updated_other_project = other_project.with_category("api", Category(dir="api/", patterns=["*.py"]))

        await session.save_project(updated_other_project)

        listener.config_changed.assert_not_awaited()
        reloaded_projects = await session.get_all_projects()
        assert "api" in reloaded_projects[other_key].categories
        assert (await session.get_project()).name == "current-project"

    @pytest.mark.anyio
    async def test_config_file_change_ignores_other_project(self, tmp_path, monkeypatch):
        """Shared config-file changes do not notify when only another project changed."""
        monkeypatch.setattr(Session, "_ensure_watcher_started", AsyncMock(return_value=None))
        session = await self._create_bound_session("current-project", str(tmp_path))
        config_manager = session._get_config_manager(str(tmp_path))
        _other_key, other_project = await config_manager.get_or_create_project_config("other-project")
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        await session.save_project(other_project.with_category("api", Category(dir="api/", patterns=["*.py"])))
        await session._on_config_file_changed(str(config_manager.config_file))

        listener.config_changed.assert_not_awaited()
        assert (await session.get_project()).name == "current-project"

    @pytest.mark.anyio
    async def test_config_file_change_notifies_for_bound_project(self, tmp_path, monkeypatch):
        """Shared config-file changes notify when the bound project changed externally."""
        monkeypatch.setattr(Session, "_ensure_watcher_started", AsyncMock(return_value=None))
        session = await self._create_bound_session("current-project", str(tmp_path))
        project = await session.get_project()
        config_manager = session._get_config_manager(str(tmp_path))
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        assert project.key is not None
        updated_project = project.with_category("docs", Category(dir="docs/", patterns=["*.md"]))
        await config_manager.save_project_config(project.key, updated_project)
        await session._on_config_file_changed(str(config_manager.config_file))

        listener.config_changed.assert_awaited_once_with(session)
        assert "docs" in (await session.get_project()).categories

    @pytest.mark.anyio
    async def test_global_feature_flag_changes_notify_config_listeners(self, tmp_path, monkeypatch):
        """Global flag writes notify because they affect resolved current-project config."""
        monkeypatch.setattr(Session, "_ensure_watcher_started", AsyncMock(return_value=None))
        session = await self._create_bound_session("current-project", str(tmp_path))
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        await session.feature_flags().set("workflow", True)

        listener.config_changed.assert_awaited_once_with(session)

    @pytest.mark.anyio
    async def test_config_file_change_notifies_for_cached_global_feature_flags(self, tmp_path, monkeypatch):
        """External global flag changes notify sessions that have resolved global flags."""
        monkeypatch.setattr(Session, "_ensure_watcher_started", AsyncMock(return_value=None))
        session = await self._create_bound_session("current-project", str(tmp_path))
        config_manager = session._get_config_manager(str(tmp_path))
        await session.get_feature_flags()
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        config_data = yaml.safe_load(config_manager.config_file.read_text())
        config_data.setdefault("feature_flags", {})["workflow"] = True
        config_manager.config_file.write_text(yaml.dump(config_data))
        await session._on_config_file_changed(str(config_manager.config_file))

        listener.config_changed.assert_awaited_once_with(session)

    @pytest.mark.anyio
    async def test_config_file_change_notifies_for_uncached_global_feature_flags(self, tmp_path, monkeypatch):
        """External global flag changes notify even before global flags are cached."""
        monkeypatch.setattr(Session, "_ensure_watcher_started", AsyncMock(return_value=None))
        session = await self._create_bound_session("current-project", str(tmp_path))
        config_manager = session._get_config_manager(str(tmp_path))
        listener = _RecordingSessionListener()
        session.add_listener(listener)

        config_data = yaml.safe_load(config_manager.config_file.read_text())
        config_data.setdefault("feature_flags", {})["workflow"] = True
        config_manager.config_file.write_text(yaml.dump(config_data))
        await session._on_config_file_changed(str(config_manager.config_file))

        listener.config_changed.assert_awaited_once_with(session)

    @pytest.mark.anyio
    async def test_file_locking_prevents_corruption(self, tmp_path, monkeypatch):
        """Test that config lock prevents read-modify-write race conditions."""
        monkeypatch.setattr("mcp_guide.file_lock.LOCK_RETRY_SECONDS", 0.01)
        monkeypatch.setattr(Session, "_ensure_watcher_started", AsyncMock(return_value=None))
        monkeypatch.setattr(Session, "_notify_config_changed", AsyncMock(return_value=None))
        # Create initial session and project
        initial_session = await self._create_bound_session("test-project", str(tmp_path))
        await initial_session.get_project()  # Create the project

        results = []
        errors = []

        async def update_project(category_name: str):
            try:
                # Each task creates its own session and updates the project
                session = await self._create_bound_session("test-project", str(tmp_path))
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

        # Verify ALL categories were saved (no data loss from race conditions)
        final_session = await self._create_bound_session("test-project", str(tmp_path))
        project = await final_session.get_project()
        assert isinstance(project.categories, dict)
        assert len(project.categories) == len(category_names), (
            f"Expected {len(category_names)} categories, got {len(project.categories)}"
        )
        assert set(project.categories.keys()) == set(category_names)
