"""Tests for Session and ContextVar integration."""

import pytest

from mcp_guide.config import ConfigManager
from mcp_guide.session import Session


class TestSession:
    """Tests for Session."""

    @pytest.mark.asyncio
    async def test_session_creation(self, tmp_path):
        """Session can be created with valid project name."""
        manager = ConfigManager(config_dir=str(tmp_path))
        await manager.get_or_create_project_config("test-project")

        session = Session(config_manager=manager, project_name="test-project")
        assert session.project_name == "test-project"

    @pytest.mark.asyncio
    async def test_session_validates_project_name(self, tmp_path):
        """Session validates project name format."""
        manager = ConfigManager(config_dir=str(tmp_path))

        # Empty name should fail
        with pytest.raises(ValueError, match="cannot be empty"):
            Session(config_manager=manager, project_name="")

        # Whitespace-only name should fail
        with pytest.raises(ValueError, match="cannot be empty"):
            Session(config_manager=manager, project_name="   ")

    @pytest.mark.asyncio
    async def test_session_rejects_invalid_characters(self, tmp_path):
        """Session should reject names with invalid characters."""
        manager = ConfigManager(config_dir=str(tmp_path))
        invalid_names = ["project@name", "project name", "project/name", "project.name", "project!"]
        for name in invalid_names:
            with pytest.raises(ValueError, match="must contain only alphanumeric"):
                Session(config_manager=manager, project_name=name)

    @pytest.mark.asyncio
    async def test_lazy_config_loading(self, tmp_path):
        """Project config is loaded lazily on first access."""
        manager = ConfigManager(config_dir=str(tmp_path))
        await manager.get_or_create_project_config("test-project")

        session = Session(config_manager=manager, project_name="test-project")

        # Config not loaded yet
        assert session._cached_project is None

        # Access triggers loading
        project = await session.get_project()
        assert project.name == "test-project"

        # Second access uses cache
        project2 = await session.get_project()
        assert project2 is project

    @pytest.mark.asyncio
    async def test_functional_config_update(self, tmp_path):
        """update_config applies functional update and saves."""
        from mcp_guide.models import Category

        manager = ConfigManager(config_dir=str(tmp_path))
        await manager.get_or_create_project_config("test-project")

        session = Session(config_manager=manager, project_name="test-project")

        category = Category(name="docs", dir="docs/", patterns=["*.md"])
        await session.update_config(lambda p: p.with_category(category))

        # Verify update was saved
        reloaded = await manager.get_or_create_project_config("test-project")
        assert len(reloaded.categories) == 1
        assert reloaded.categories[0].name == "docs"

    @pytest.mark.asyncio
    async def test_get_state_returns_mutable_state(self, tmp_path):
        """get_state returns mutable SessionState."""
        manager = ConfigManager(config_dir=str(tmp_path))
        await manager.get_or_create_project_config("test-project")

        session = Session(config_manager=manager, project_name="test-project")
        state = session.get_state()

        state.current_dir = "/test/path"
        assert session.get_state().current_dir == "/test/path"


class TestContextVar:
    """Tests for ContextVar session tracking."""

    @pytest.mark.asyncio
    async def test_get_current_session(self, tmp_path):
        """get_current_session returns session from ContextVar."""
        from mcp_guide.session import get_current_session, set_current_session

        manager = ConfigManager(config_dir=str(tmp_path))
        await manager.get_or_create_project_config("test-project")

        session = Session(config_manager=manager, project_name="test-project")
        set_current_session(session)

        retrieved = get_current_session("test-project")
        assert retrieved is session

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, tmp_path):
        """get_current_session returns None for nonexistent session."""
        from mcp_guide.session import get_current_session

        result = get_current_session("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_remove_current_session(self, tmp_path):
        """remove_current_session removes session from ContextVar."""
        from mcp_guide.session import (
            get_current_session,
            remove_current_session,
            set_current_session,
        )

        manager = ConfigManager(config_dir=str(tmp_path))
        await manager.get_or_create_project_config("test-project")

        session = Session(config_manager=manager, project_name="test-project")
        set_current_session(session)

        remove_current_session("test-project")

        result = get_current_session("test-project")
        assert result is None

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, tmp_path):
        """ContextVar provides isolation between async tasks."""
        import asyncio

        from mcp_guide.session import get_current_session, set_current_session

        manager = ConfigManager(config_dir=str(tmp_path))
        await manager.get_or_create_project_config("project1")
        await manager.get_or_create_project_config("project2")

        async def task1():
            session1 = Session(config_manager=manager, project_name="project1")
            set_current_session(session1)
            await asyncio.sleep(0.01)
            retrieved = get_current_session("project1")
            assert retrieved is session1
            assert get_current_session("project2") is None

        async def task2():
            session2 = Session(config_manager=manager, project_name="project2")
            set_current_session(session2)
            await asyncio.sleep(0.01)
            retrieved = get_current_session("project2")
            assert retrieved is session2
            assert get_current_session("project1") is None

        await asyncio.gather(task1(), task2())
