"""Integration tests for config and session management."""

import asyncio

import pytest

from mcp_guide.config import ConfigManager
from mcp_guide.models import Category
from mcp_guide.session import Session, get_current_session, set_current_session


class TestConfigSessionIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, tmp_path):
        """Test complete workflow: create session, update config, save, reload."""
        # Create project
        manager = ConfigManager(config_dir=str(tmp_path))
        project = await manager.get_or_create_project_config("test-project")
        assert len(project.categories) == 0

        # Create session
        session = Session(_config_manager=manager, project_name="test-project")
        set_current_session(session)

        # Update config through session
        category = Category(dir="docs/", patterns=["*.md"])
        await session.update_config(lambda p: p.with_category("docs", category))

        # Verify update persisted
        reloaded_project = await manager.get_or_create_project_config("test-project")
        assert len(reloaded_project.categories) == 1

        # Verify session cache updated
        cached_project = await session.get_project()
        assert len(cached_project.categories) == 1

    @pytest.mark.asyncio
    async def test_concurrent_sessions_different_projects(self, tmp_path):
        """Test concurrent sessions on different projects work correctly."""
        manager = ConfigManager(config_dir=str(tmp_path))
        await manager.get_or_create_project_config("project1")
        await manager.get_or_create_project_config("project2")

        results = []

        async def task1():
            session1 = Session(_config_manager=manager, project_name="project1")
            set_current_session(session1)

            category = Category(dir="api/", patterns=["*.py"])
            await session1.update_config(lambda p: p.with_category("api", category))

            await asyncio.sleep(0.01)

            retrieved = get_current_session("project1")
            assert retrieved is session1
            project = await retrieved.get_project()
            results.append(("task1", len(project.categories)))

        async def task2():
            session2 = Session(_config_manager=manager, project_name="project2")
            set_current_session(session2)

            category = Category(dir="web/", patterns=["*.html"])
            await session2.update_config(lambda p: p.with_category("web", category))

            await asyncio.sleep(0.01)

            retrieved = get_current_session("project2")
            assert retrieved is session2
            project = await retrieved.get_project()
            results.append(("task2", len(project.categories)))

        await asyncio.gather(task1(), task2())

        # Verify both tasks completed successfully
        assert len(results) == 2
        assert all(count == 1 for _, count in results)

        # Verify both projects were updated independently
        project1 = await manager.get_or_create_project_config("project1")
        project2 = await manager.get_or_create_project_config("project2")
        assert len(project1.categories) == 1
        assert len(project2.categories) == 1

    @pytest.mark.asyncio
    async def test_file_locking_prevents_corruption(self, tmp_path):
        """Test that config lock prevents read-modify-write race conditions."""
        manager = ConfigManager(config_dir=str(tmp_path))
        await manager.get_or_create_project_config("test-project")

        results = []
        errors = []

        async def update_project(category_name: str):
            try:
                # Each task reads current state, adds category, and saves
                project = await manager.get_or_create_project_config("test-project")
                category = Category(dir=f"{category_name}/", patterns=["*.md"])
                updated = project.with_category(category_name, category)
                await manager.save_project_config(updated)
                results.append(category_name)
            except Exception as e:
                errors.append(str(e))

        # Create multiple tasks updating the same project
        tasks = [update_project(f"cat{i}") for i in range(5)]

        await asyncio.gather(*tasks)

        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Verify all tasks completed
        assert len(results) == 5

        # Verify ALL categories were saved (no data loss from race conditions)
        project = await manager.get_or_create_project_config("test-project")
        assert isinstance(project.categories, dict)
        assert len(project.categories) == 5, f"Expected 5 categories, got {len(project.categories)}"
        category_names = set(project.categories.keys())
        assert category_names == {"cat0", "cat1", "cat2", "cat3", "cat4"}
