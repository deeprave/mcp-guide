"""Tests for Session and ContextVar integration."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

import mcp_guide.session
from mcp_guide.config import ConfigManager
from mcp_guide.session import (
    CachedRootsInfo,
    Session,
    get_or_create_session,
    set_current_session,
    set_project,
)


class TestSetProject:
    """Tests for set_project tool function."""

    @pytest.mark.asyncio
    async def test_set_project_creates_and_loads(self, tmp_path, monkeypatch):
        """set_project creates/loads project successfully."""
        monkeypatch.setattr(
            "mcp_guide.session.ConfigManager", lambda config_dir=None: ConfigManager(config_dir=str(tmp_path))
        )

        result = await set_project("new-project")

        assert result.is_ok()
        assert result.value.name == "new-project"

    @pytest.mark.asyncio
    async def test_set_project_with_invalid_name(self, tmp_path, monkeypatch):
        """set_project returns error for invalid project name."""
        from mcp_guide.tools.tool_constants import ERROR_INVALID_NAME

        monkeypatch.setattr(
            "mcp_guide.session.ConfigManager", lambda config_dir=None: ConfigManager(config_dir=str(tmp_path))
        )

        result = await set_project("invalid@name")

        assert result.is_failure()
        assert result.error_type == ERROR_INVALID_NAME


class TestGetOrCreateSession:
    """Tests for get_or_create_session function."""

    @pytest.mark.asyncio
    async def test_creates_session_with_explicit_name(self, tmp_path, monkeypatch):
        """Creates session when explicit project_name provided."""
        monkeypatch.setattr(
            "mcp_guide.session.ConfigManager", lambda config_dir=None: ConfigManager(config_dir=str(tmp_path))
        )

        session = await get_or_create_session(project_name="explicit-project", _config_dir_for_tests=str(tmp_path))
        assert session.project_name == "explicit-project"

    @pytest.mark.asyncio
    async def test_creates_session_from_context(self, tmp_path, monkeypatch):
        """Creates session by detecting name from context."""
        monkeypatch.setattr(
            "mcp_guide.session.ConfigManager", lambda config_dir=None: ConfigManager(config_dir=str(tmp_path))
        )

        mock_ctx = MagicMock()
        mock_root = MagicMock()
        mock_root.uri = "file:///home/user/detected-project"
        mock_ctx.session.list_roots = AsyncMock(return_value=MagicMock(roots=[mock_root]))

        session = await get_or_create_session(ctx=mock_ctx)
        assert session.project_name == "detected-project"

    @pytest.mark.asyncio
    async def test_returns_existing_session(self, tmp_path, monkeypatch):
        """Returns existing session if already created."""
        monkeypatch.setattr(
            "mcp_guide.session.ConfigManager", lambda config_dir=None: ConfigManager(config_dir=str(tmp_path))
        )

        session1 = await get_or_create_session(project_name="same-project")
        session2 = await get_or_create_session(project_name="same-project")

        assert session1 is session2

    @pytest.mark.asyncio
    async def test_creates_different_sessions_for_different_projects(self, tmp_path, monkeypatch):
        """Creates separate sessions for different projects."""
        monkeypatch.setattr(
            "mcp_guide.session.ConfigManager", lambda config_dir=None: ConfigManager(config_dir=str(tmp_path))
        )

        session1 = await get_or_create_session(project_name="project1")
        session2 = await get_or_create_session(project_name="project2")

        assert session1 is not session2
        assert session1.project_name == "project1"
        assert session2.project_name == "project2"


class TestProjectNameDetection:
    """Tests for _determine_project_name function."""

    @pytest.mark.asyncio
    async def test_determine_from_client_roots(self):
        """Project name determined from MCP client roots (PRIMARY)."""
        # Mock Context with roots
        mock_ctx = MagicMock()
        mock_root = MagicMock()
        mock_root.uri = "file:///home/user/my-project"
        mock_ctx.session.list_roots = AsyncMock(return_value=MagicMock(roots=[mock_root]))

        project_name = await mcp_guide.session._determine_project_name(mock_ctx)
        assert project_name == "my-project"

    @pytest.mark.asyncio
    async def test_determine_from_pwd_fallback(self, monkeypatch):
        """Project name determined from PWD as LAST FALLBACK."""
        monkeypatch.setenv("PWD", "/home/user/test-project")

        # No context provided
        project_name = await mcp_guide.session._determine_project_name(None)
        assert project_name == "test-project"

    @pytest.mark.asyncio
    async def test_pwd_must_be_absolute(self, monkeypatch):
        """PWD must be absolute path - reject relative paths."""
        monkeypatch.setenv("PWD", "./relative/path")

        with pytest.raises(ValueError, match="Project context not available"):
            await mcp_guide.session._determine_project_name(None)

    @pytest.mark.asyncio
    async def test_error_when_no_source_available(self, monkeypatch):
        """Raises ValueError with instruction when no source available."""
        monkeypatch.delenv("PWD", raising=False)

        with pytest.raises(ValueError, match="Call set_project"):
            await mcp_guide.session._determine_project_name(None)

    @pytest.mark.asyncio
    async def test_handles_client_roots_exception(self, monkeypatch):
        """Gracefully handles exception from client roots."""
        monkeypatch.setenv("PWD", "/home/user/fallback-project")

        # Mock Context that raises exception
        mock_ctx = MagicMock()
        mock_ctx.session.list_roots = AsyncMock(side_effect=Exception("Client error"))

        # Should fall back to PWD
        project_name = await mcp_guide.session._determine_project_name(mock_ctx)
        assert project_name == "fallback-project"

    @pytest.mark.asyncio
    async def test_caches_roots_info(self):
        """Caches entire roots list and derived project name."""
        import mcp_guide.session

        # Reset cache (ContextVar)
        mcp_guide.session._cached_roots.set(None)

        mock_ctx = MagicMock()
        mock_root = MagicMock()
        mock_root.uri = "file:///home/user/cached-project"
        mock_ctx.session.list_roots = AsyncMock(return_value=MagicMock(roots=[mock_root]))

        await mcp_guide.session._determine_project_name(mock_ctx)

        # Check cache was populated
        cached = mcp_guide.session._cached_roots.get()
        assert cached is not None
        assert cached.project_name == "cached-project"
        assert len(cached.roots) == 1


class TestCachedRootsInfo:
    """Tests for CachedRootsInfo dataclass."""

    def test_cached_roots_info_creation(self):
        """CachedRootsInfo can be created with roots, project_name, and timestamp."""
        roots = [{"uri": "file:///test/project", "name": "Test Project"}]
        cache = CachedRootsInfo(roots=roots, project_name="project", timestamp=1234567890.0)

        assert cache.roots == roots
        assert cache.project_name == "project"
        assert cache.timestamp == 1234567890.0


class TestSession:
    """Tests for Session."""

    @pytest.mark.asyncio
    async def test_session_creation(self, tmp_path):
        """Session can be created with valid project name."""
        session = await get_or_create_session(project_name="test-project", _config_dir_for_tests=str(tmp_path))
        assert session.project_name == "test-project"

    @pytest.mark.asyncio
    async def test_session_validates_project_name(self, tmp_path):
        """Session validates project name format."""
        manager = ConfigManager(config_dir=str(tmp_path))

        # Empty name should fail
        with pytest.raises(ValueError, match="cannot be empty"):
            await get_or_create_session(project_name="")

        # Whitespace-only name should fail
        with pytest.raises(ValueError, match="cannot be empty"):
            await get_or_create_session(project_name="   ")

    @pytest.mark.asyncio
    async def test_session_rejects_invalid_characters(self, tmp_path):
        """Session should reject names with invalid characters."""
        manager = ConfigManager(config_dir=str(tmp_path))
        invalid_names = ["project@name", "project name", "project/name", "project.name", "project!"]
        for name in invalid_names:
            with pytest.raises(ValueError, match="must contain only alphanumeric"):
                await get_or_create_session(project_name=name)

    @pytest.mark.asyncio
    async def test_lazy_config_loading(self, tmp_path):
        """Project config is loaded lazily on first access."""
        session = await get_or_create_session(project_name="test-project", _config_dir_for_tests=str(tmp_path))

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
        from mcp_guide.config import ConfigManager
        from mcp_guide.models import Category

        # Create session with tmp_path-backed config manager for test isolation
        manager = ConfigManager(config_dir=str(tmp_path))
        await manager.get_or_create_project_config("test-project")

        session = Session(_config_manager=manager, project_name="test-project")
        set_current_session(session)

        category = Category(name="docs", dir="docs/", patterns=["*.md"])
        await session.update_config(lambda p: p.with_category(category))

        # Verify update was saved by reloading from disk (same tmp_path)
        reloaded = await manager.get_or_create_project_config("test-project")
        assert len(reloaded.categories) == 1
        assert reloaded.categories[0].name == "docs"

    @pytest.mark.asyncio
    async def test_get_state_returns_mutable_state(self, tmp_path):
        """get_state returns mutable SessionState."""
        session = await get_or_create_session(project_name="test-project", _config_dir_for_tests=str(tmp_path))
        state = session.get_state()

        state.current_dir = "/test/path"
        assert session.get_state().current_dir == "/test/path"


class TestContextVar:
    """Tests for ContextVar session tracking."""

    @pytest.mark.asyncio
    async def test_get_current_session(self, tmp_path):
        """get_current_session returns session from ContextVar."""
        from mcp_guide.session import get_current_session, set_current_session

        session = await get_or_create_session(project_name="test-project", _config_dir_for_tests=str(tmp_path))
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

        session = await get_or_create_session(project_name="test-project", _config_dir_for_tests=str(tmp_path))
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
            session1 = await get_or_create_session(project_name="project1")
            set_current_session(session1)
            await asyncio.sleep(0.01)
            retrieved = get_current_session("project1")
            assert retrieved is session1
            assert get_current_session("project2") is None

        async def task2():
            session2 = await get_or_create_session(project_name="project2")
            set_current_session(session2)
            await asyncio.sleep(0.01)
            retrieved = get_current_session("project2")
            assert retrieved is session2
            assert get_current_session("project1") is None

        await asyncio.gather(task1(), task2())
