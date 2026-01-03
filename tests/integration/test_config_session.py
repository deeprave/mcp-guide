"""Integration tests for config and session management."""

import asyncio

import pytest

from mcp_guide.models import Category
from mcp_guide.session import Session, get_current_session, set_current_session


class TestConfigSessionIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, tmp_path):
        """Test complete workflow: create session, update config, save, reload."""
        # Create session with test config directory
        session = Session("test-project", _config_dir_for_tests=str(tmp_path))
        set_current_session(session)

        # Get initial project (should have no categories)
        project = await session.get_project()
        assert len(project.categories) == 0

        # Update config through session
        category = Category(dir="docs/", patterns=["*.md"])
        await session.update_config(lambda p: p.with_category("docs", category))

        # Verify update persisted by creating new session
        new_session = Session("test-project", _config_dir_for_tests=str(tmp_path))
        reloaded_project = await new_session.get_project()
        assert len(reloaded_project.categories) == 1

        # Verify session cache updated
        cached_project = await session.get_project()
        assert len(cached_project.categories) == 1

    @pytest.mark.asyncio
    async def test_concurrent_sessions_different_projects(self, tmp_path):
        """Test concurrent sessions on different projects work correctly."""
        results = []

        async def task1():
            session1 = Session("project1", _config_dir_for_tests=str(tmp_path))
            set_current_session(session1)

            category = Category(dir="api/", patterns=["*.py"])
            await session1.update_config(lambda p: p.with_category("api", category))

            await asyncio.sleep(0.01)

            retrieved = get_current_session("project1")
            assert retrieved is session1
            project = await retrieved.get_project()
            results.append(("task1", len(project.categories)))

        async def task2():
            session2 = Session("project2", _config_dir_for_tests=str(tmp_path))
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

        # Verify both projects were updated independently by creating new sessions
        session1_verify = Session("project1", _config_dir_for_tests=str(tmp_path))
        session2_verify = Session("project2", _config_dir_for_tests=str(tmp_path))

        project1 = await session1_verify.get_project()
        project2 = await session2_verify.get_project()
        assert len(project1.categories) == 1
        assert len(project2.categories) == 1

    @pytest.mark.asyncio
    async def test_file_locking_prevents_corruption(self, tmp_path):
        """Test that config lock prevents read-modify-write race conditions."""
        # Create initial session and project
        initial_session = Session("test-project", _config_dir_for_tests=str(tmp_path))
        await initial_session.get_project()  # Create the project

        results = []
        errors = []

        async def update_project(category_name: str):
            try:
                # Each task creates its own session and updates the project
                session = Session("test-project", _config_dir_for_tests=str(tmp_path))
                category = Category(dir=f"{category_name}/", patterns=["*.md"])
                await session.update_config(lambda p: p.with_category(category_name, category))
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
        final_session = Session("test-project", _config_dir_for_tests=str(tmp_path))
        project = await final_session.get_project()
        assert isinstance(project.categories, dict)
        assert len(project.categories) == 5, f"Expected 5 categories, got {len(project.categories)}"
        category_names = set(project.categories.keys())
        assert category_names == {"cat0", "cat1", "cat2", "cat3", "cat4"}
