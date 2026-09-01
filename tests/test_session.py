"""Tests for Session lifecycle and runtime ownership."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_guide.runtime import GuideRuntime, OwnerKey
from mcp_guide.session import (
    Session,
    get_session,
    request_session_scope,
    set_project,
)
from tests.helpers import create_test_runtime, create_unbound_test_session


def runtime_context(tmp_path: Path, request_id: str = "test-request") -> tuple[GuideRuntime[Session], MagicMock]:
    """Create a modern request context with an isolated runtime-owned Session."""
    runtime = create_test_runtime(str(tmp_path))
    ctx = MagicMock()
    ctx.request_context.protocol_version = "2026-07-28"
    ctx.request_context.request_id = request_id
    ctx.request_context.meta = None
    ctx.request_context.lifespan_context = runtime
    ctx.session.client_params = None
    return runtime, ctx


class TestSetProject:
    """Tests for set_project tool function."""

    @pytest.mark.anyio
    async def test_set_project_creates_and_loads(self, tmp_path, monkeypatch):
        """set_project creates/loads project successfully."""
        _runtime, ctx = runtime_context(tmp_path)
        result = await set_project("/client/workspace/new-project", ctx, session_id="new-project-session")

        assert result.is_ok()
        assert result.value is not None
        assert result.value.name == "new-project"

    @pytest.mark.anyio
    async def test_set_project_with_invalid_name(self, tmp_path, monkeypatch):
        """set_project returns error for invalid project name."""
        from mcp_guide.result_constants import ERROR_INVALID_NAME

        _runtime, ctx = runtime_context(tmp_path)
        result = await set_project("relative/invalid@name", ctx, session_id="invalid-project-session")

        assert result.is_failure()
        assert result.error_type == ERROR_INVALID_NAME

    @pytest.mark.anyio
    async def test_set_project_rejects_second_binding(self, tmp_path, monkeypatch):
        """A Session root is immutable after the first explicit binding."""
        _runtime, ctx = runtime_context(tmp_path)
        assert (await set_project("/client/workspace/first-project", ctx, session_id="binding-session")).is_ok()
        result = await set_project("/client/workspace/second-project", ctx, session_id="binding-session")

        assert result.is_failure()
        assert "already bound" in (result.error or "")

    @pytest.mark.anyio
    async def test_set_project_binds_the_explicit_runtime_session(self, tmp_path, monkeypatch):
        """Modern binding updates the Session selected by the supplied FastMCP ID."""
        runtime, ctx = runtime_context(tmp_path, "set-project-request")

        result = await set_project("/client/workspace/runtime-project", ctx, session_id="runtime-session")

        assert result.is_ok()
        session = runtime.resolve_session(OwnerKey("runtime-session"))
        assert session.bound_root_path == Path("/client/workspace/runtime-project")


class TestGetOrCreateSession:
    """Tests for get_session function."""

    def test_session_requires_a_runtime_owned_configuration_service(self) -> None:
        """A Session cannot create or select a configuration service for itself."""
        with pytest.raises(TypeError, match="runtime"):
            Session()  # ty: ignore[missing-argument]

    @pytest.mark.anyio
    async def test_creates_session_with_explicit_name(self, tmp_path, monkeypatch):
        """Creates session when explicit project_name provided."""
        from mcp_guide.models import Project

        async def mock_switch_project(self, project_name):
            self._Session__delegate.bind(Project(name=project_name, categories={}, collections={}))

        monkeypatch.setattr(Session, "switch_project", mock_switch_project)
        monkeypatch.setattr(Session, "add_listener", lambda self, listener: None)

        session = await get_session(project_name="explicit-project", _config_dir_for_tests=str(tmp_path))
        assert session.project_name == "explicit-project"

    @pytest.mark.anyio
    async def test_context_does_not_bind_a_project_from_client_roots(self, tmp_path, monkeypatch):
        """Remote context metadata never determines a client filesystem root."""
        _runtime, mock_ctx = runtime_context(tmp_path)
        mock_ctx.transport = "streamable-http"

        session = await get_session(ctx=mock_ctx)
        assert session.project_is_bound is False

    @pytest.mark.anyio
    async def test_stdio_context_with_session_id_does_not_bind_from_inherited_pwd(self, tmp_path, monkeypatch):
        """An explicit session ID never permits PWD project inference."""
        _runtime, mock_ctx = runtime_context(tmp_path)
        monkeypatch.setenv("PWD", "/client/workspace/stdio-project")
        mock_ctx.transport = "stdio"

        session = await get_session(ctx=mock_ctx, session_id="stdio-session")
        assert session.project_is_bound is False

    @pytest.mark.anyio
    async def test_set_project_uses_explicit_path_when_stdio_has_pwd(self, tmp_path, monkeypatch):
        """Explicit binding takes precedence over inherited PWD."""
        _runtime, ctx = runtime_context(tmp_path)
        ctx.transport = "stdio"
        monkeypatch.setenv("PWD", "/client/workspace/stdio-project")

        result = await set_project("/client/workspace/explicit-project", ctx, session_id="stdio-session")

        assert result.is_ok()
        assert result.value is not None
        assert result.value.name == "explicit-project"

    @pytest.mark.anyio
    async def test_request_scope_reuses_and_releases_unbound_session(self, tmp_path, monkeypatch):
        """An unbound Session is shared only for one request."""
        runtime, ctx = runtime_context(tmp_path)
        async with request_session_scope(ctx, "same-session") as session1:
            session2 = await get_session(ctx=ctx, session_id="same-session")
            assert session1 is session2

        assert runtime.find_session(OwnerKey("same-session")) is None

    @pytest.mark.anyio
    async def test_runtime_session_receives_standard_listeners(self, tmp_path):
        """Runtime resolution preserves the creation-path listener contract."""
        runtime = create_test_runtime(str(tmp_path))
        runtime_session = runtime.resolve_session(OwnerKey("runtime-session"))
        mock_ctx = MagicMock()
        mock_ctx.request_context.protocol_version = "2026-07-28"
        mock_ctx.request_context.request_id = "runtime-request"
        mock_ctx.request_context.meta = None
        mock_ctx.request_context.lifespan_context = runtime
        mock_ctx.session.client_params = None

        session = await get_session(ctx=mock_ctx, session_id="runtime-session")

        assert session is runtime_session
        assert getattr(session, "_guide_listeners_attached") is True

    @pytest.mark.anyio
    async def test_runtime_keeps_explicit_session_owners_isolated(self, tmp_path):
        """Explicit session IDs select separate runtime-owned Sessions."""
        runtime = create_test_runtime(str(tmp_path))

        def context(request_id: str):
            ctx = MagicMock()
            ctx.request_context.protocol_version = "2026-07-28"
            ctx.request_context.request_id = request_id
            ctx.request_context.meta = None
            ctx.request_context.lifespan_context = runtime
            ctx.session.client_params = None
            return ctx

        first = await get_session(ctx=context("first-request"), session_id="first-session")
        second = await get_session(ctx=context("second-request"), session_id="second-session")

        assert first is not second

    @pytest.mark.anyio
    async def test_request_scope_uses_legacy_fastmcp_session_id(self, tmp_path):
        """Legacy request scopes use FastMCP's public connection ID as their owner."""
        runtime = create_test_runtime(str(tmp_path))
        ctx = MagicMock()
        ctx.request_context.protocol_version = "2025-06-18"
        ctx.request_context.request_id = "legacy-request"
        ctx.request_context.meta = None
        ctx.request_context.lifespan_context = runtime
        ctx.session.client_params = None
        ctx.session_id = "legacy-fastmcp-session"

        async with request_session_scope(ctx) as session:
            assert session is await get_session(ctx=ctx)

        assert runtime.find_session(OwnerKey("legacy-fastmcp-session")) is None

    @pytest.mark.anyio
    async def test_project_name_bootstrap_is_test_local(self, tmp_path):
        """Test-only project-name bootstrap does not create global session state."""
        session1 = await get_session(project_name="project1", _config_dir_for_tests=str(tmp_path))
        session2 = await get_session(project_name="project2", _config_dir_for_tests=str(tmp_path))

        assert session1 is not session2
        assert session1.project_name == "project1"
        assert session2.project_name == "project2"

    @pytest.mark.anyio
    async def test_project_switch_regenerates_startup_instructions_after_restart(self, tmp_path, monkeypatch):
        """Switching projects clears stale queued instructions, then queues fresh startup guidance."""
        from mcp_guide.decorators import clear_registered_tasks_for_testing
        from mcp_guide.task_manager.manager import TaskManager

        await TaskManager._reset_for_testing()
        clear_registered_tasks_for_testing()

        startup_rendered: list[str] = []
        guide_rendered: list[str] = []

        async def render_startup_content(session, *, pattern, category_dir):
            content = f"{pattern}:{len(startup_rendered)}"
            startup_rendered.append(content)
            rendered = MagicMock()
            rendered.content = content
            return rendered

        async def render_guide_content(session, *, pattern, category_dir):
            content = f"{pattern}:{len(guide_rendered)}"
            guide_rendered.append(content)
            rendered = MagicMock()
            rendered.content = content
            return rendered

        monkeypatch.setattr("mcp_guide.startup_listener.render_content", render_startup_content)
        monkeypatch.setattr("mcp_guide.guide_uri_listener.render_content", render_guide_content)

        session = await get_session(project_name="project-one", _config_dir_for_tests=str(tmp_path))
        task_manager = session.task_manager
        initial_instructions = list(task_manager._pending_instructions)
        await task_manager.queue_instruction("stale project instruction")

        await session.switch_project("project-two")

        assert "stale project instruction" not in task_manager._pending_instructions
        for instruction in initial_instructions:
            assert instruction not in task_manager._pending_instructions

        pending_instructions = list(task_manager._pending_instructions)
        assert any(instruction.startswith("_startup:") for instruction in pending_instructions)
        assert any(instruction.startswith("_onboard_prompt:") for instruction in pending_instructions)
        assert any(instruction.startswith("_guide-uri:") for instruction in pending_instructions)

        await TaskManager._reset_for_testing()


class TestUnboundSession:
    """Tests for unbound session lifecycle."""

    def test_session_starts_unbound(self, tmp_path):
        """Session created without project is unbound."""
        from mcp_guide.models.delegate import UNBOUND_PROJECT_NAME

        session = create_unbound_test_session(str(tmp_path))
        assert session.project_is_bound is False
        assert session.project_name == UNBOUND_PROJECT_NAME

    @pytest.mark.anyio
    async def test_get_project_raises_when_unbound(self, tmp_path):
        """get_project raises NoProjectError on unbound session."""
        from mcp_guide.models.exceptions import NoProjectError

        session = create_unbound_test_session(str(tmp_path))
        with pytest.raises(NoProjectError):
            await session.get_project()

    @pytest.mark.anyio
    async def test_switch_project_requires_a_bound_root(self, tmp_path, monkeypatch):
        """switch_project changes configuration only; set_project binds the root."""
        session = create_unbound_test_session(str(tmp_path))
        assert session.project_is_bound is False

        with pytest.raises(ValueError, match="explicitly bound root"):
            await session.switch_project("test-project")
        assert session.project_is_bound is False
