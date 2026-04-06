"""Integration tests for config and session management."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from mcp_guide.models import Category
from mcp_guide.session import Session, set_current_session


class TestConfigSessionIntegration:
    """End-to-end integration tests."""

    @staticmethod
    async def _create_bound_session(project_name: str, config_dir: str) -> Session:
        """Create a session bound directly to a project without switch notifications."""
        session = Session(_config_dir_for_tests=config_dir)
        config_manager = session._get_config_manager(config_dir)
        _key, project = await config_manager.get_or_create_project_config(project_name)
        session._Session__delegate.bind(project)
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
            results.append(("task1", len(session1._Session__delegate.project.categories)))

        async def task2():
            session2 = await self._create_bound_session("project2", config_dir)

            category = Category(dir="web/", patterns=["*.html"])
            await session2.update_config(lambda p: p.with_category("web", category))
            results.append(("task2", len(session2._Session__delegate.project.categories)))

        await asyncio.gather(task1(), task2())

        # Verify both tasks completed successfully
        assert len(results) == 2
        assert all(count == 1 for _, count in results)

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
