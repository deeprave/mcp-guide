"""Tests for Session and ContextVar integration."""

from unittest.mock import AsyncMock, MagicMock

import pytest

import mcp_guide.session
from mcp_guide.session import (
    Session,
    get_session,
    set_project,
)


class TestSetProject:
    """Tests for set_project tool function."""

    @pytest.mark.anyio
    async def test_set_project_creates_and_loads(self, tmp_path, monkeypatch):
        """set_project creates/loads project successfully."""
        await mcp_guide.session.remove_current_session()
        original_session_init = Session.__init__

        def mock_session_init(self, *, _config_dir_for_tests=None):
            return original_session_init(self, _config_dir_for_tests=str(tmp_path))

        monkeypatch.setattr(Session, "__init__", mock_session_init)

        result = await set_project("new-project")

        assert result.is_ok()
        assert result.value.name == "new-project"

    @pytest.mark.anyio
    async def test_set_project_with_invalid_name(self, tmp_path, monkeypatch):
        """set_project returns error for invalid project name."""
        from mcp_guide.result_constants import ERROR_INVALID_NAME

        await mcp_guide.session.remove_current_session()
        original_session_init = Session.__init__

        def mock_session_init(self, *, _config_dir_for_tests=None):
            return original_session_init(self, _config_dir_for_tests=str(tmp_path))

        monkeypatch.setattr(Session, "__init__", mock_session_init)

        result = await set_project("invalid@name")

        assert result.is_failure()
        assert result.error_type == ERROR_INVALID_NAME


class TestGetOrCreateSession:
    """Tests for get_session function."""

    @pytest.mark.anyio
    async def test_creates_session_with_explicit_name(self, tmp_path, monkeypatch):
        """Creates session when explicit project_name provided."""
        from mcp_guide.models import Project

        original_session_init = Session.__init__

        def mock_session_init(self, *, _config_dir_for_tests=None):
            return original_session_init(self, _config_dir_for_tests=str(tmp_path))

        async def mock_switch_project(self, project_name):
            self._Session__delegate.bind(Project(name=project_name, categories={}, collections={}))

        monkeypatch.setattr(Session, "__init__", mock_session_init)
        monkeypatch.setattr(Session, "switch_project", mock_switch_project)
        monkeypatch.setattr(Session, "add_listener", lambda self, listener: None)

        session = await get_session(project_name="explicit-project", _config_dir_for_tests=str(tmp_path))
        assert session.project_name == "explicit-project"

    @pytest.mark.anyio
    async def test_creates_session_from_context(self, tmp_path, monkeypatch):
        """Creates session by detecting name from context."""
        from mcp_guide.models import Project

        original_session_init = Session.__init__

        def mock_session_init(self, *, _config_dir_for_tests=None):
            return original_session_init(self, _config_dir_for_tests=str(tmp_path))

        async def mock_switch_project(self, project_name):
            self._Session__delegate.bind(Project(name=project_name, categories={}, collections={}))

        monkeypatch.setattr(Session, "__init__", mock_session_init)
        monkeypatch.setattr(Session, "switch_project", mock_switch_project)
        monkeypatch.setattr(Session, "add_listener", lambda self, listener: None)

        mock_ctx = MagicMock()
        mock_root = MagicMock()
        mock_root.uri = "file:///home/user/detected-project"
        mock_ctx.session.list_roots = AsyncMock(return_value=MagicMock(roots=[mock_root]))

        session = await get_session(ctx=mock_ctx)
        assert session.project_name == "detected-project"

    @pytest.mark.anyio
    async def test_returns_existing_session(self, tmp_path, monkeypatch):
        """Returns existing session if already created."""
        original_session_init = Session.__init__

        def mock_session_init(self, *, _config_dir_for_tests=None):
            return original_session_init(self, _config_dir_for_tests=str(tmp_path))

        monkeypatch.setattr(Session, "__init__", mock_session_init)

        session1 = await get_session(project_name="same-project")
        session2 = await get_session(project_name="same-project")

        assert session1 is session2

    @pytest.mark.anyio
    async def test_returns_same_session_ignoring_project_name(self, tmp_path, monkeypatch):
        """Second call returns existing session regardless of project_name."""
        original_session_init = Session.__init__

        def mock_session_init(self, *, _config_dir_for_tests=None):
            return original_session_init(self, _config_dir_for_tests=str(tmp_path))

        monkeypatch.setattr(Session, "__init__", mock_session_init)

        session1 = await get_session(project_name="project1")
        session2 = await get_session(project_name="project2")

        assert session1 is session2
        assert session1.project_name == "project1"


class TestProjectNameDetection:
    """Tests for cache_mcp_globals function."""

    @pytest.mark.anyio
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

    @pytest.mark.anyio
    async def test_determine_from_pwd_fallback(self, monkeypatch):
        """Project name determined from PWD as LAST FALLBACK."""
        monkeypatch.setenv("PWD", "/home/user/test-project")

        # No context provided
        cached = await mcp_guide.mcp_context.cache_mcp_globals(None)
        assert cached is False

        project_name = await mcp_guide.mcp_context.resolve_project_name()
        assert project_name == "test-project"

    @pytest.mark.anyio
    async def test_pwd_must_be_absolute(self, monkeypatch):
        """PWD must be absolute path - reject relative paths."""
        monkeypatch.setenv("PWD", "./relative/path")

        with pytest.raises(ValueError, match="Project context not available"):
            await mcp_guide.mcp_context.resolve_project_name()

    @pytest.mark.anyio
    async def test_error_when_no_source_available(self, monkeypatch):
        """Raises ValueError with instruction when no source available."""
        monkeypatch.delenv("PWD", raising=False)

        with pytest.raises(ValueError, match="Call set_project"):
            await mcp_guide.mcp_context.resolve_project_name()

    @pytest.mark.anyio
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

    @pytest.mark.anyio
    async def test_caches_roots_info(self):
        """Caches entire roots list in bootstrap cache when no session exists."""
        import mcp_guide.mcp_context

        # Clear bootstrap cache
        mcp_guide.mcp_context._bootstrap_roots.set([])

        mock_ctx = MagicMock()
        mock_root = MagicMock()
        mock_root.uri = "file:///home/user/cached-project"
        mock_ctx.session.list_roots = AsyncMock(return_value=MagicMock(roots=[mock_root]))

        await mcp_guide.mcp_context.cache_mcp_globals(mock_ctx)

        # Check bootstrap cache was populated with roots
        cached_roots = mcp_guide.mcp_context._bootstrap_roots.get()
        assert len(cached_roots) == 1
        assert str(cached_roots[0].uri) == "file:///home/user/cached-project"


class TestUnboundSession:
    """Tests for unbound session lifecycle."""

    def test_session_starts_unbound(self):
        """Session created without project is unbound."""
        from mcp_guide.models.delegate import UNBOUND_PROJECT_NAME

        session = Session()
        assert session.project_is_bound is False
        assert session.project_name == UNBOUND_PROJECT_NAME

    @pytest.mark.anyio
    async def test_get_project_raises_when_unbound(self):
        """get_project raises NoProjectError on unbound session."""
        from mcp_guide.models.exceptions import NoProjectError

        session = Session()
        with pytest.raises(NoProjectError):
            await session.get_project()

    @pytest.mark.anyio
    async def test_switch_project_binds_session(self, tmp_path, monkeypatch):
        """switch_project binds an unbound session."""
        original_session_init = Session.__init__

        def mock_session_init(self, *, _config_dir_for_tests=None):
            return original_session_init(self, _config_dir_for_tests=str(tmp_path))

        monkeypatch.setattr(Session, "__init__", mock_session_init)

        session = Session()
        assert session.project_is_bound is False

        await session.switch_project("test-project")
        assert session.project_is_bound is True
        assert session.project_name == "test-project"

    @pytest.mark.anyio
    async def test_unbound_session_binds_when_ctx_arrives(self, tmp_path, monkeypatch):
        """Unbound session binds when get_session is called with ctx."""
        from mcp_guide.models import Project

        await mcp_guide.session.remove_current_session()
        monkeypatch.delenv("PWD", raising=False)
        monkeypatch.delenv("CWD", raising=False)

        original_session_init = Session.__init__

        def mock_session_init(self, *, _config_dir_for_tests=None):
            return original_session_init(self, _config_dir_for_tests=str(tmp_path))

        async def mock_switch_project(self, project_name):
            self._Session__delegate.bind(Project(name=project_name, categories={}, collections={}))

        monkeypatch.setattr(Session, "__init__", mock_session_init)
        monkeypatch.setattr(Session, "switch_project", mock_switch_project)
        monkeypatch.setattr(Session, "add_listener", lambda self, listener: None)

        # First call without ctx — creates unbound session
        session = await get_session(_config_dir_for_tests=str(tmp_path))
        assert session.project_is_bound is False

        # Second call with ctx providing roots — triggers binding
        mock_ctx = MagicMock()
        mock_root = MagicMock()
        mock_root.uri = (tmp_path / "my-project").as_uri()
        mock_ctx.session.list_roots = AsyncMock(return_value=MagicMock(roots=[mock_root]))

        session2 = await get_session(ctx=mock_ctx, _config_dir_for_tests=str(tmp_path))
        assert session2 is session
        assert session.project_is_bound is True
        assert session.project_name == "my-project"


class TestTryBindFromRoots:
    """Tests for Session.try_bind_from_roots edge cases."""

    @pytest.mark.anyio
    async def test_no_project_name_from_roots(self, tmp_path, monkeypatch):
        """No project name resolved — roots updated, no switch, returns current bound state."""
        session = Session(_config_dir_for_tests=str(tmp_path))
        monkeypatch.setattr("mcp_guide.mcp_context.project_name_from_roots", lambda roots: None)

        result = await session.try_bind_from_roots(["file:///some/path"])

        assert session.roots == ["file:///some/path"]
        assert result is False  # still unbound

    @pytest.mark.anyio
    async def test_same_project_name_no_switch(self, tmp_path, monkeypatch):
        """Resolved name matches current project — switch_project not called."""
        from mcp_guide.models import Project

        session = Session(_config_dir_for_tests=str(tmp_path))
        session._Session__delegate.bind(Project(name="my-project", categories={}, collections={}))
        monkeypatch.setattr("mcp_guide.mcp_context.project_name_from_roots", lambda roots: "my-project")
        session.switch_project = AsyncMock(side_effect=AssertionError("should not be called"))

        result = await session.try_bind_from_roots(["file:///home/user/my-project"])

        assert result is True
        assert session.roots == ["file:///home/user/my-project"]

    @pytest.mark.anyio
    async def test_switch_project_error_swallowed(self, tmp_path, monkeypatch):
        """switch_project raises — warning logged, returns current bound state."""
        session = Session(_config_dir_for_tests=str(tmp_path))
        monkeypatch.setattr("mcp_guide.mcp_context.project_name_from_roots", lambda roots: "bad-project")
        monkeypatch.setattr(session, "switch_project", AsyncMock(side_effect=ValueError("config error")))
        warning = MagicMock()
        monkeypatch.setattr("mcp_guide.session.logger.warning", warning)

        result = await session.try_bind_from_roots(["file:///home/user/bad-project"])

        assert result is False  # still unbound
        warning.assert_called_once()
        assert "Failed to bind/switch" in warning.call_args.args[0]

    @pytest.mark.anyio
    async def test_binds_unbound_session(self, tmp_path, monkeypatch):
        """Unbound session with valid roots binds successfully."""
        session = Session(_config_dir_for_tests=str(tmp_path))
        mock_root = MagicMock()
        mock_root.uri = "file:///home/user/new-project"
        monkeypatch.setattr("mcp_guide.mcp_context.project_name_from_roots", lambda roots: "new-project")

        result = await session.try_bind_from_roots([mock_root])

        assert result is True
        assert session.project_is_bound is True
        assert session.project_name == "new-project"
