"""Tests for Session and ContextVar integration."""

from unittest.mock import AsyncMock, MagicMock

import pytest

import mcp_guide.session
from mcp_guide.config import ConfigManager
from mcp_guide.session import (
    get_or_create_session,
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
        from mcp_guide.result_constants import ERROR_INVALID_NAME

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
    """Tests for cache_mcp_globals function."""

    @pytest.mark.asyncio
    async def test_determine_from_client_roots(self):
        """Project name determined from MCP client roots (PRIMARY)."""
        # Mock Context with roots
        mock_ctx = MagicMock()
        mock_root = MagicMock()
        mock_root.uri = "file:///home/user/my-project"
        mock_ctx.session.list_roots = AsyncMock(return_value=MagicMock(roots=[mock_root]))

        cached = await mcp_guide.mcp_context.cache_mcp_globals(mock_ctx)
        assert cached is True

        project_name = await mcp_guide.mcp_context.resolve_project_name()
        assert project_name == "my-project"

    @pytest.mark.asyncio
    async def test_determine_from_pwd_fallback(self, monkeypatch):
        """Project name determined from PWD as LAST FALLBACK."""
        monkeypatch.setenv("PWD", "/home/user/test-project")

        # No context provided
        cached = await mcp_guide.mcp_context.cache_mcp_globals(None)
        assert cached is False

        project_name = await mcp_guide.mcp_context.resolve_project_name()
        assert project_name == "test-project"

    @pytest.mark.asyncio
    async def test_pwd_must_be_absolute(self, monkeypatch):
        """PWD must be absolute path - reject relative paths."""
        monkeypatch.setenv("PWD", "./relative/path")

        with pytest.raises(ValueError, match="Project context not available"):
            await mcp_guide.mcp_context.resolve_project_name()

    @pytest.mark.asyncio
    async def test_error_when_no_source_available(self, monkeypatch):
        """Raises ValueError with instruction when no source available."""
        monkeypatch.delenv("PWD", raising=False)

        with pytest.raises(ValueError, match="Call set_project"):
            await mcp_guide.mcp_context.resolve_project_name()

    @pytest.mark.asyncio
    async def test_handles_client_roots_exception(self, monkeypatch):
        """Gracefully handles exception from client roots."""
        monkeypatch.setenv("PWD", "/home/user/fallback-project")

        # Mock Context that raises exception
        mock_ctx = MagicMock()
        mock_ctx.session.list_roots = AsyncMock(side_effect=Exception("Client error"))

        # Should still cache successfully (agent info can be cached even if roots fail)
        cached = await mcp_guide.mcp_context.cache_mcp_globals(mock_ctx)
        assert cached is True

        project_name = await mcp_guide.mcp_context.resolve_project_name()
        assert project_name == "fallback-project"

    @pytest.mark.asyncio
    async def test_caches_roots_info(self):
        """Caches entire roots list and derived project name."""
        import mcp_guide.session

        # Reset cache (ContextVar)
        mcp_guide.mcp_context.cached_mcp_context.set(None)

        mock_ctx = MagicMock()
        mock_root = MagicMock()
        mock_root.uri = "file:///home/user/cached-project"
        mock_ctx.session.list_roots = AsyncMock(return_value=MagicMock(roots=[mock_root]))

        await mcp_guide.mcp_context.cache_mcp_globals(mock_ctx)

        # Check cache was populated with roots (project name is resolved separately)
        cached = mcp_guide.mcp_context.cached_mcp_context.get()
        assert cached is not None
        assert len(cached.roots) == 1
        assert str(cached.roots[0].uri) == "file:///home/user/cached-project"
        # Project name is empty until _resolve_project_name is called
        assert cached.project_name == ""
