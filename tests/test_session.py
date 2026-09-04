"""Tests for Session lifecycle and runtime ownership."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_guide.runtime import GuideRuntime, OwnerKey
from mcp_guide.session import (
    Session,
    bind_session_project,
    request_context_scope,
)
from tests.helpers import create_test_runtime, create_test_session, create_unbound_test_session


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
    """Tests for explicit project binding."""

    @pytest.mark.anyio
    async def test_set_project_creates_and_loads(self, tmp_path, monkeypatch):
        """Binding creates/loads project successfully."""
        _runtime, ctx = runtime_context(tmp_path)
        async with request_context_scope(
            ctx, "new-project-session", allow_pwd_bootstrap=False, mint_session_if_unbound=True
        ) as request_context:
            project = await bind_session_project(request_context.session, "/client/workspace/new-project")

        assert project.name == "new-project"

    @pytest.mark.anyio
    async def test_set_project_with_invalid_name(self, tmp_path, monkeypatch):
        """Binding raises for an invalid project name."""
        from mcp_guide.validation import InvalidProjectNameError

        _runtime, ctx = runtime_context(tmp_path)
        async with request_context_scope(
            ctx, "invalid-project-session", allow_pwd_bootstrap=False, mint_session_if_unbound=True
        ) as request_context:
            with pytest.raises(InvalidProjectNameError):
                await bind_session_project(request_context.session, "relative/invalid@name")

    @pytest.mark.anyio
    async def test_set_project_rejects_second_binding(self, tmp_path, monkeypatch):
        """A Session root is immutable after the first explicit binding."""
        _runtime, ctx = runtime_context(tmp_path)
        async with request_context_scope(
            ctx, "binding-session", allow_pwd_bootstrap=False, mint_session_if_unbound=True
        ) as request_context:
            await bind_session_project(request_context.session, "/client/workspace/first-project")
            with pytest.raises(ValueError, match="already bound"):
                await bind_session_project(request_context.session, "/client/workspace/second-project")

    @pytest.mark.anyio
    async def test_set_project_binds_the_explicit_runtime_session(self, tmp_path, monkeypatch):
        """Modern binding updates the Session selected by the supplied FastMCP ID."""
        runtime, ctx = runtime_context(tmp_path, "set-project-request")

        async with request_context_scope(
            ctx, "runtime-session", allow_pwd_bootstrap=False, mint_session_if_unbound=True
        ) as request_context:
            await bind_session_project(request_context.session, "/client/workspace/runtime-project")

        session = runtime.resolve_session(OwnerKey("runtime-session"))
        assert session.bound_root_path == Path("/client/workspace/runtime-project")

    @pytest.mark.anyio
    async def test_unmintable_legacy_set_project_raises_typed_error(self, tmp_path, monkeypatch):
        """A legacy client with no connection session cannot mint via set_project."""
        from types import SimpleNamespace

        import mcp_guide.session as session_module
        from mcp_guide.session import UnmintableGuideSessionError

        class FakeContext:
            def __init__(self, runtime) -> None:
                self.request_context = SimpleNamespace(
                    protocol_version="legacy",
                    request_id="unmintable-set-project",
                    meta=None,
                    lifespan_context=runtime,
                )
                self.session = SimpleNamespace(client_params=None)
                self.session_id = None
                self.transport = "streamable-http"

        runtime = create_test_runtime(str(tmp_path))
        monkeypatch.setattr(session_module, "Context", FakeContext)

        with pytest.raises(UnmintableGuideSessionError, match="cannot carry a Guide session"):
            async with request_context_scope(
                FakeContext(runtime), allow_pwd_bootstrap=False, mint_session_if_unbound=True
            ):
                pass


class TestGetOrCreateSession:
    """Tests for public session resolution."""

    def test_session_requires_a_runtime_owned_configuration_service(self) -> None:
        """A Session cannot create or select a configuration service for itself."""
        with pytest.raises(TypeError, match="runtime"):
            Session()  # ty: ignore[missing-argument]

    @pytest.mark.anyio
    async def test_creates_session_with_explicit_name(self, runtime, tmp_path, monkeypatch):
        """Creates session when explicit project_name provided."""
        session = await create_test_session(runtime, "explicit-project")
        assert session.project_name == "explicit-project"

    @pytest.mark.anyio
    async def test_context_does_not_bind_a_project_from_client_roots(self, tmp_path, monkeypatch):
        """Remote context metadata never determines a client filesystem root."""
        _runtime, mock_ctx = runtime_context(tmp_path)
        mock_ctx.transport = "streamable-http"

        async with request_context_scope(mock_ctx, allow_pwd_bootstrap=False) as request_context:
            assert request_context.session.project_is_bound is False

    @pytest.mark.anyio
    async def test_stdio_context_with_session_id_does_not_bind_from_inherited_pwd(self, tmp_path, monkeypatch):
        """An explicit session ID never permits PWD project inference."""
        _runtime, mock_ctx = runtime_context(tmp_path)
        monkeypatch.setenv("PWD", "/client/workspace/stdio-project")
        mock_ctx.transport = "stdio"

        async with request_context_scope(mock_ctx, "stdio-session", allow_pwd_bootstrap=True) as request_context:
            assert request_context.session.project_is_bound is False

    @pytest.mark.anyio
    async def test_set_project_uses_explicit_path_when_stdio_has_pwd(self, tmp_path, monkeypatch):
        """Explicit binding takes precedence over inherited PWD."""
        _runtime, ctx = runtime_context(tmp_path)
        ctx.transport = "stdio"
        monkeypatch.setenv("PWD", "/client/workspace/stdio-project")

        async with request_context_scope(
            ctx, "stdio-session", allow_pwd_bootstrap=False, mint_session_if_unbound=True
        ) as request_context:
            project = await bind_session_project(request_context.session, "/client/workspace/explicit-project")

        assert project.name == "explicit-project"

    @pytest.mark.anyio
    async def test_request_scope_reuses_and_releases_unbound_session(self, tmp_path, monkeypatch):
        """An unbound Session is shared only for one request."""
        runtime, ctx = runtime_context(tmp_path)
        async with request_context_scope(ctx, "same-session", allow_pwd_bootstrap=False) as request_context:
            assert request_context.session is runtime.get_current_session("same-session")

        assert runtime.find_session(OwnerKey("same-session")) is None

    @pytest.mark.anyio
    async def test_request_context_scope_constructs_one_context_from_the_runtime_session(self, tmp_path):
        """The transport boundary supplies the exact resolved Session downstream."""
        runtime, ctx = runtime_context(tmp_path)

        async with request_context_scope(ctx, "request-context-session", allow_pwd_bootstrap=False) as context:
            assert context.session is runtime.find_session(OwnerKey("request-context-session"))
            assert context.session_id == "request-context-session"
            assert context.root is None
            assert context.project is None

    @pytest.mark.anyio
    async def test_stdio_pwd_bootstrap_does_not_retain_unbound_owner(self, tmp_path, monkeypatch):
        """A PWD-bound Session is retained only under its minted id, never unbound:*."""
        from types import SimpleNamespace
        from unittest.mock import AsyncMock

        import fastmcp.server.sessions as fastmcp_sessions

        import mcp_guide.session as session_module

        class FakeContext:
            def __init__(self, runtime) -> None:
                self.request_context = SimpleNamespace(
                    protocol_version="2026-07-28",
                    request_id="stdio-pwd",
                    meta=None,
                    lifespan_context=runtime,
                )
                self.session = SimpleNamespace(client_params=None)
                self.session_id = None
                self.transport = "stdio"

        project_root = tmp_path / "stdio-project"
        project_root.mkdir()
        monkeypatch.setenv("PWD", str(project_root))
        runtime = create_test_runtime(str(tmp_path / "config"))
        monkeypatch.setattr(session_module, "Context", FakeContext)
        monkeypatch.setattr(fastmcp_sessions, "create_session", AsyncMock(return_value="minted-stdio-session"))
        monkeypatch.setattr(fastmcp_sessions, "get_session", AsyncMock(return_value=object()))

        async with request_context_scope(FakeContext(runtime), allow_pwd_bootstrap=True) as request_context:
            assert request_context.session.project_is_bound is True

        assert not any(key.value.startswith("unbound:") for key in runtime._sessions)
        assert OwnerKey("minted-stdio-session") in runtime._sessions

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

        async with request_context_scope(mock_ctx, "runtime-session", allow_pwd_bootstrap=False) as request_context:
            session = request_context.session

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

        async with request_context_scope(
            context("first-request"), "first-session", allow_pwd_bootstrap=False
        ) as first_context:
            first = first_context.session
        async with request_context_scope(
            context("second-request"), "second-session", allow_pwd_bootstrap=False
        ) as second_context:
            second = second_context.session

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

        async with request_context_scope(ctx, allow_pwd_bootstrap=False) as request_context:
            assert request_context.session is runtime.get_current_session("legacy-fastmcp-session")

        assert runtime.find_session(OwnerKey("legacy-fastmcp-session")) is None

    @pytest.mark.anyio
    async def test_project_name_bootstrap_is_test_local(self, runtime, tmp_path):
        """Test-only project-name bootstrap does not create global session state."""
        session1 = await create_test_session(runtime, "project1")
        session2 = await create_test_session(runtime, "project2")

        assert session1 is not session2
        assert session1.project_name == "project1"
        assert session2.project_name == "project2"

    @pytest.mark.anyio
    async def test_project_switch_regenerates_startup_instructions_after_restart(self, runtime, tmp_path, monkeypatch):
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

        session = await create_test_session(runtime, "project-one")
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

    def test_session_starts_unbound(self, runtime, tmp_path):
        """Session created without project is unbound."""
        from mcp_guide.models.delegate import UNBOUND_PROJECT_NAME

        session = create_unbound_test_session(runtime)
        assert session.project_is_bound is False
        assert session.project_name == UNBOUND_PROJECT_NAME

    @pytest.mark.anyio
    async def test_get_project_raises_when_unbound(self, runtime, tmp_path):
        """get_project raises NoProjectError on unbound session."""
        from mcp_guide.models.exceptions import NoProjectError

        session = create_unbound_test_session(runtime)
        with pytest.raises(NoProjectError):
            await session.get_project()

    @pytest.mark.anyio
    async def test_switch_project_requires_a_bound_root(self, runtime, tmp_path, monkeypatch):
        """switch_project changes configuration only; set_project binds the root."""
        session = create_unbound_test_session(runtime)
        assert session.project_is_bound is False

        with pytest.raises(ValueError, match="explicitly bound root"):
            await session.switch_project("test-project")
        assert session.project_is_bound is False
