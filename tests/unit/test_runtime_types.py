"""Framework-neutral runtime type contracts."""

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from tests.helpers import create_test_runtime, request_context_for

from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.mcp_context import runtime_from_fastmcp, session_resolution_from_fastmcp
from mcp_guide.models import Project
from mcp_guide.runtime import (
    GuideRuntime,
    OwnerKey,
    RequestContext,
    RootIdentity,
    create_runtime,
    get_runtime,
)
from mcp_guide.utils.project_hash import calculate_project_hash


def test_use_pwd_is_off_unless_explicitly_enabled(monkeypatch) -> None:
    """Process PWD binding is launch-opt-in, never implied by an unset flag."""
    from mcp_guide.session import use_pwd_enabled

    monkeypatch.delenv("MG_USE_PWD", raising=False)
    assert use_pwd_enabled() is False
    monkeypatch.setenv("MG_USE_PWD", "0")
    assert use_pwd_enabled() is False
    monkeypatch.setenv("MG_USE_PWD", "1")
    assert use_pwd_enabled() is True
    monkeypatch.setenv("MG_USE_PWD", "true")
    assert use_pwd_enabled() is True


def runtime_for_config(config_dir):
    """Create a runtime that owns configuration for ``config_dir``."""
    return create_test_runtime(str(config_dir))


def _resolve(relative_path):
    return Path("/docs") / relative_path


def context_for(session, session_id: str | None = "session-1") -> RequestContext:
    """Build a RequestContext without going through FastMCP."""
    return RequestContext(
        session_id=session_id,
        session=session,  # type: ignore[arg-type]
        seq=1,
        document_path_resolver=_resolve,
    )


def test_request_context_carries_only_resolved_application_state() -> None:
    """Request context carries the exact Session, root, and active Project."""
    root = RootIdentity.from_path("/client/workspace/demo")
    project = Project(name="review", key=f"review-{root.hash[:8]}", hash=root.hash)

    session = SimpleNamespace(project=project, bound_root_path="/client/workspace/demo")
    context = context_for(session, "session-42")

    assert context.root == root
    assert context.project is project
    assert context.project.hash == calculate_project_hash("/client/workspace/demo")
    assert context.session is session
    assert context.session_id == "session-42"


def test_request_context_records_the_fastmcp_session_id_when_supplied() -> None:
    """The resolved context retains the client-provided session identity."""
    context = context_for(SimpleNamespace(project=None, bound_root_path=None), "session-43")

    assert context.session_id == "session-43"


@pytest.mark.parametrize("session_id", ["", "session\n43", "session\x0043", "x" * 513])
def test_request_context_rejects_unsafe_session_ids(session_id: str) -> None:
    """Session identifiers are unstructured but safe for registry use and logging."""
    with pytest.raises(ValueError, match="session ID"):
        context_for(SimpleNamespace(project=None, bound_root_path=None), session_id)


@pytest.mark.anyio
async def test_request_context_constructs_from_the_resolved_session(tmp_path) -> None:
    """Context construction reads the Session's exact bound root and Project."""

    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("session-44"))
    await session.bind_project_path("/client/workspace/context-project")

    context = await request_context_for(session, "session-44")

    assert context.session is session
    assert context.session_id == "session-44"
    assert context.root == RootIdentity.from_path("/client/workspace/context-project")
    assert context.project is await session.get_project()


def test_session_does_not_publish_runtime(tmp_path) -> None:
    """Session keeps GuideRuntime private; process code uses get_runtime()."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("private-runtime"))
    assert not hasattr(type(session), "runtime")
    assert get_runtime() is runtime


@pytest.mark.anyio
async def test_stop_releases_the_process_runtime_for_a_successor(tmp_path) -> None:
    """Stopping the singleton is the only way a later runtime may be constructed."""
    first = runtime_for_config(tmp_path)
    await first.stop()
    with pytest.raises(RuntimeError, match="has not been created"):
        get_runtime()
    second = runtime_for_config(tmp_path / "successor")
    assert get_runtime() is second
    await second.stop()


@pytest.mark.anyio
async def test_start_reinstalls_the_process_runtime_after_stop(tmp_path) -> None:
    """FastMCP lifespan start reclaims the process slot after stop() released it."""
    runtime = create_runtime(lambda _owner: object(), config_dir=str(tmp_path))
    await runtime.start()
    await runtime.stop()
    with pytest.raises(RuntimeError, match="has not been created"):
        get_runtime()
    await runtime.start()
    assert get_runtime() is runtime
    await runtime.stop()


def test_create_runtime_refuses_a_second_install(tmp_path) -> None:
    """A live process runtime cannot be replaced without stop()."""
    create_runtime(lambda _owner: object(), config_dir=str(tmp_path))
    with pytest.raises(RuntimeError, match="already exists"):
        create_runtime(lambda _owner: object(), config_dir=str(tmp_path / "second"))


@pytest.mark.anyio
async def test_request_context_resolves_only_safe_document_relative_paths(tmp_path) -> None:
    """Application code can resolve a document path without receiving docroot."""
    docroot = tmp_path / "documents"
    runtime = create_runtime(lambda _owner: object(), config_dir=str(tmp_path), docroot=docroot)

    class ContextSession:
        def __init__(self) -> None:
            self.project = None

    context = await runtime.request_context(ContextSession(), session_id=None, seq=1)

    assert not hasattr(context, "document_root")
    resolver = context.get_docroot_resolver()
    assert resolver("guides/intro.md") == (docroot / "guides" / "intro.md").resolve()
    assert resolver("guides/outro.md") == (docroot / "guides" / "outro.md").resolve()
    assert context.resolve_document_path("guides/intro.md") == (docroot / "guides" / "intro.md").resolve()
    assert resolver("guides/intro.md").is_absolute()
    inside = (docroot / "guides" / "intro.md").resolve()
    assert context.resolve_document_path(inside) == inside
    with pytest.raises(ValueError, match="within"):
        context.resolve_document_path("/tmp/outside.md")
    with pytest.raises(ValueError, match="within"):
        context.resolve_document_path("../outside.md")


@pytest.mark.anyio
async def test_resolve_document_path_does_not_follow_docroot_symlink(tmp_path) -> None:
    """Containment stays lexical; the returned path is the resolved filesystem location."""
    from mcp_guide.config_paths import get_config_file

    real_docs = tmp_path / "templates"
    real_docs.mkdir()
    docroot = tmp_path / "docs"
    docroot.symlink_to(real_docs)
    config_file = get_config_file(str(tmp_path))
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(f"docroot: {docroot}\nprojects: {{}}\n", encoding="utf-8")
    runtime = create_runtime(lambda _owner: object(), config_dir=str(tmp_path))

    class ContextSession:
        def __init__(self) -> None:
            self.project = None

    context = await runtime.request_context(ContextSession(), session_id=None, seq=1)
    resolved = context.resolve_document_path("intro.md")
    assert resolved.is_absolute()
    assert resolved == (docroot / "intro.md").resolve()
    with pytest.raises(ValueError, match="within"):
        context.resolve_document_path("../outside.md")


@pytest.mark.anyio
async def test_request_context_project_tracks_session_rebind(tmp_path) -> None:
    """RequestContext.project is the Session's current object, not a frozen snapshot."""
    from dataclasses import replace

    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("session-45"))
    await session.bind_project_path("/client/workspace/first")
    context = await request_context_for(session, "session-45")
    first = context.project
    await session.update_config(lambda project: replace(project, collections=dict(project.collections)))

    assert context.project is await session.get_project()
    assert context.project is not first


@pytest.mark.anyio
async def test_request_context_root_tracks_in_request_bind(tmp_path) -> None:
    """RequestContext.root and is_bound follow the Session after an in-request bind."""
    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("bind-live"))
    context = await request_context_for(session, "bind-live")

    from mcp_guide.models.exceptions import NoProjectError

    assert not context.is_bound
    assert context.root is None
    with pytest.raises(NoProjectError, match="no bound project root"):
        context.require_root()

    await session.bind_project_path("/client/workspace/live-root")

    assert context.is_bound
    assert context.root is not None
    assert context.root.path == "/client/workspace/live-root"
    assert context.require_root().path == "/client/workspace/live-root"
    assert context.require_project() is session.project


@pytest.mark.anyio
async def test_get_session_and_project_reloads_a_dirty_project(tmp_path) -> None:
    """Helper-backed tools reload when the Session has marked its Project stale."""
    from mcp_guide.tools.tool_helpers import get_session_and_project

    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("dirty-project"))
    await session.bind_project_path("/client/workspace/dirty-project")
    context = await request_context_for(session, "dirty-project")
    original_invalidate = session.invalidate_cache
    reloads: list[bool] = []

    async def tracking_invalidate() -> None:
        reloads.append(True)
        await original_invalidate()

    session._project_dirty = True
    session.invalidate_cache = tracking_invalidate  # type: ignore[method-assign]
    helper_session, project = await get_session_and_project(context)

    assert helper_session is session
    assert project is await session.get_project()
    assert reloads == [True]
    assert session._project_dirty is False


@pytest.mark.anyio
async def test_request_context_scope_requires_fastmcp_context() -> None:
    """Missing FastMCP context is a hard error, not an ambient Session fallback."""
    from mcp_guide.session import request_context_scope

    with pytest.raises(RuntimeError, match="FastMCP context"):
        async with request_context_scope(None, allow_pwd_bootstrap=False):
            pass


@pytest.mark.anyio
async def test_request_context_scope_requires_runtime() -> None:
    """A FastMCP context without GuideRuntime is a hard error."""
    from mcp_guide.session import request_context_scope

    ctx = SimpleNamespace(request_context=SimpleNamespace(lifespan_context=None))
    with pytest.raises(RuntimeError, match="GuideRuntime"):
        async with request_context_scope(ctx, allow_pwd_bootstrap=False):
            pass


@pytest.mark.anyio
async def test_prompt_wrapper_requires_fastmcp_context() -> None:
    """Prompt adapters fail clearly when invoked without a FastMCP context."""
    from mcp_guide.core.prompt_decorator import _PROMPT_REGISTRY, promptfunc

    @promptfunc()
    async def review_cycle_prompt(*, request_context: RequestContext) -> dict:
        return {"ok": True}

    try:
        with pytest.raises(RuntimeError, match="FastMCP context"):
            await review_cycle_prompt()
    finally:
        _PROMPT_REGISTRY.pop("review_cycle_prompt", None)


@pytest.mark.anyio
async def test_resource_wrapper_requires_fastmcp_context() -> None:
    """Resource adapters fail clearly when invoked without a FastMCP context."""
    from mcp_guide.core.resource_decorator import _RESOURCE_REGISTRY, resourcefunc

    @resourcefunc("guide://review-cycle-resource")
    async def review_cycle_resource(*, request_context: RequestContext, request_uri: str | None) -> dict:
        return {"ok": True}

    try:
        with pytest.raises(RuntimeError, match="FastMCP context"):
            await review_cycle_resource()
    finally:
        _RESOURCE_REGISTRY.pop("review_cycle_resource", None)


def test_root_identity_rejects_relative_client_path() -> None:
    """A root identity cannot be fabricated from an ambiguous client path."""
    with pytest.raises(ValueError, match="absolute"):
        RootIdentity.from_path("demo")


def test_root_identity_expands_user_anchored_client_path(tmp_path, monkeypatch) -> None:
    """A root identity is derived from an expanded user-anchored path."""
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))

    identity = RootIdentity.from_path("~/demo")

    assert identity.path == str(home / "demo")
    assert identity.name == "demo"
    assert identity.hash == calculate_project_hash(str(home / "demo"))


def test_runtime_resolves_sessions_by_explicit_owner() -> None:
    """The global runtime owns a registry instead of using MCP connection objects."""
    created: list[object] = []

    def create_session(_owner: OwnerKey) -> object:
        session = object()
        created.append(session)
        return session

    runtime = create_runtime(session_factory=create_session)

    first = runtime.resolve_session(OwnerKey("agent-a"))
    same_owner = runtime.resolve_session(OwnerKey("agent-a"))
    other_owner = runtime.resolve_session(OwnerKey("agent-b"))

    assert first is same_owner
    assert other_owner is not first
    assert len(created) == 2


@pytest.mark.anyio
async def test_runtime_lifecycle_runs_once_and_stops_once() -> None:
    """The FastMCP lifespan can own Guide initialization without construction side effects."""
    events: list[str] = []

    async def on_start() -> None:
        events.append("start")

    async def on_stop() -> None:
        events.append("stop")

    runtime = create_runtime(lambda _owner: object(), on_start=on_start, on_stop=on_stop)
    assert not runtime.started

    await runtime.start()
    await runtime.start()
    assert runtime.started
    assert events == ["start"]

    await runtime.stop()
    await runtime.stop()
    assert not runtime.started
    assert events == ["start", "stop"]


@pytest.mark.anyio
async def test_runtime_delegates_docroot_to_its_configuration_service(tmp_path) -> None:
    """The configuration service remains the sole docroot owner."""
    (tmp_path / "config.yaml").write_text("docroot: /configured/docs\nprojects: {}\n")
    runtime = create_runtime(lambda _owner: object(), config_dir=str(tmp_path))

    await runtime.start()
    assert await runtime.get_docroot() == "/configured/docs"
    await runtime.stop()


def test_session_obtains_its_configuration_service_from_its_runtime(tmp_path) -> None:
    """Session keeps only its runtime, not a duplicate configuration reference."""
    from mcp_guide.session import Session

    runtime: GuideRuntime[Session]

    def create_session(_owner: OwnerKey) -> Session:
        return Session(runtime)

    runtime = create_runtime(create_session, config_dir=str(tmp_path))
    session = runtime.resolve_session(OwnerKey("test-owner"))

    assert session._config() is runtime.configuration_service()
    assert not hasattr(session, "_config_manager")
    assert not hasattr(session, "_Session__config_manager")


@pytest.mark.anyio
async def test_runtime_shutdown_cleans_up_its_sessions() -> None:
    """Runtime shutdown owns cleanup for Sessions created by its factory."""
    events: list[str] = []

    class TestSession:
        async def cleanup(self) -> None:
            events.append("cleanup")

    runtime = create_runtime(lambda _owner: TestSession())
    first = runtime.resolve_session(OwnerKey("first"))
    runtime.resolve_session(OwnerKey("second"))

    await runtime.start()
    await runtime.stop()

    assert events == ["cleanup", "cleanup"]
    assert runtime.resolve_session(OwnerKey("first")) is not first


@pytest.mark.anyio
async def test_runtime_shutdown_continues_after_a_session_cleanup_failure(tmp_path) -> None:
    """A failed cleanup cannot prevent shared runtime shutdown."""
    events: list[str] = []

    class FailingSession:
        async def cleanup(self) -> None:
            events.append("failing-cleanup")
            raise RuntimeError("cleanup failed")

    class HealthySession:
        async def cleanup(self) -> None:
            events.append("healthy-cleanup")

    sessions = [FailingSession(), HealthySession()]
    runtime = create_runtime(lambda _owner: sessions.pop(0), config_dir=str(tmp_path))
    runtime.resolve_session(OwnerKey("failing"))
    runtime.resolve_session(OwnerKey("healthy"))
    await runtime.start()

    with pytest.raises(RuntimeError, match="cleanup failed"):
        await runtime.stop()

    assert events == ["failing-cleanup", "healthy-cleanup"]
    assert not runtime.started


@pytest.mark.anyio
async def test_runtime_expires_inactive_sessions_with_their_owned_state() -> None:
    """Expired owners are cleaned up and resolve as fresh isolated Sessions."""
    events: list[str] = []

    class TestSession:
        async def cleanup(self) -> None:
            events.append("cleanup")

    runtime = create_runtime(lambda _owner: TestSession(), session_idle_timeout=10)
    original = runtime.resolve_session(OwnerKey("expired-owner"))

    assert await runtime.expire_inactive_sessions(now=10**12) == 1
    assert events == ["cleanup"]
    assert runtime.resolve_session(OwnerKey("expired-owner")) is not original


@pytest.mark.anyio
async def test_runtime_discards_a_failed_session_binding_immediately() -> None:
    """An invalidated FastMCP owner must not retain Guide-owned state until expiry."""
    events: list[str] = []

    class TestSession:
        async def cleanup(self) -> None:
            events.append("cleanup")

    runtime = create_runtime(lambda _owner: TestSession())
    owner = OwnerKey("failed-binding")
    original = runtime.resolve_session(owner)

    await runtime.discard_session(owner)

    assert events == ["cleanup"]
    assert runtime.resolve_session(owner) is not original


@pytest.mark.anyio
async def test_runtime_does_not_expire_an_in_flight_session() -> None:
    """An active request lease prevents its Session from being cleaned up."""
    cleaned: list[str] = []

    class SessionWithCleanup:
        async def cleanup(self) -> None:
            cleaned.append("cleaned")

    runtime = create_runtime(lambda _owner: SessionWithCleanup(), session_idle_timeout=1)
    owner = OwnerKey("active-owner")
    runtime.resolve_session(owner)

    async with runtime.session_lease(owner):
        assert await runtime.expire_inactive_sessions(now=10**12) == 0
        assert not cleaned

    assert await runtime.expire_inactive_sessions(now=10**12) == 1
    assert cleaned == ["cleaned"]


@pytest.mark.anyio
async def test_runtime_lifespan_yields_the_runtime_for_request_adapters() -> None:
    """FastMCP lifespan context can carry GuideRuntime without a global lookup."""
    runtime = create_runtime(lambda _owner: object())

    async with runtime.lifespan() as lifespan_context:
        assert lifespan_context is runtime
        assert runtime.started

    assert not runtime.started


def test_session_resolution_uses_explicit_id_for_modern_request() -> None:
    """Modern state is keyed only by the explicit, validated tool argument."""
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(
            protocol_version="2026-07-28",
            request_id="request-45",
            meta={"io.modelcontextprotocol/clientInfo": {"name": "Cursor", "version": "1.0"}},
        ),
        session=SimpleNamespace(client_params=None),
    )

    protocol_revision, resolved_session_id = session_resolution_from_fastmcp(ctx, session_id="fastmcp-session-45")

    assert protocol_revision == "2026-07-28"
    assert resolved_session_id == "fastmcp-session-45"


def test_session_resolution_does_not_make_modern_state_without_an_explicit_id() -> None:
    """A modern request without session state remains unbound for this request."""
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(protocol_version="2026-07-28", request_id="request-46", meta=None),
        session=SimpleNamespace(client_params=None),
    )

    _, resolved_session_id = session_resolution_from_fastmcp(ctx)

    assert resolved_session_id is None


def test_session_resolution_uses_public_legacy_connection_id() -> None:
    """Retained handshake clients retain their public FastMCP connection identity."""
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(protocol_version="2025-06-18", request_id="request-47", meta=None),
        session_id="legacy-session-47",
        session=SimpleNamespace(client_params={"clientInfo": {"name": "Legacy", "version": "2.0"}}),
    )

    protocol_revision, resolved_session_id = session_resolution_from_fastmcp(ctx)

    assert protocol_revision == "2025-06-18"
    assert resolved_session_id == "legacy-session-47"


def test_all_tool_arguments_advertise_an_optional_session_id() -> None:
    """The session identifier is a standard tool fixture, not per-tool boilerplate."""
    schema = ToolArguments.model_json_schema()

    assert "session_id" in schema["properties"]
    assert "session_id" not in schema.get("required", [])


def test_runtime_adapter_reads_the_public_lifespan_context() -> None:
    """Request handling obtains its runtime from FastMCP, not a module singleton."""
    runtime = create_runtime(lambda _owner: object())
    ctx = SimpleNamespace(request_context=SimpleNamespace(lifespan_context=runtime))

    assert runtime_from_fastmcp(ctx) is runtime


@pytest.mark.anyio
async def test_runtime_session_resolution_isolated_by_modern_and_legacy_owner(tmp_path) -> None:
    """Bound modern and legacy owners resolve isolated runtime Sessions."""
    from mcp_guide.session import Session, bind_session_project, request_context_scope

    runtime: GuideRuntime[Session]
    runtime = runtime_for_config(tmp_path)

    def context(protocol_version: str, request_id: str, session_id: str | None = None):
        return SimpleNamespace(
            request_context=SimpleNamespace(
                protocol_version=protocol_version,
                request_id=request_id,
                meta=None,
                lifespan_context=runtime,
            ),
            session=SimpleNamespace(client_params=None),
            session_id=session_id,
        )

    async def bind(ctx, path: str, session_id: str | None = None):
        async with request_context_scope(ctx, session_id, allow_pwd_bootstrap=False) as request_context:
            await bind_session_project(request_context.session, path)
            return request_context.session

    try:
        modern_first_context = context("2026-07-28", "modern-1")
        modern_first = await bind(modern_first_context, "/client/workspace/modern", "modern-owner")
        async with request_context_scope(
            context("2026-07-28", "modern-2"), "modern-owner", allow_pwd_bootstrap=False
        ) as modern_same_context:
            modern_same = modern_same_context.session
        modern_other_context = context("2026-07-28", "modern-3")
        modern_other = await bind(modern_other_context, "/client/workspace/other", "other-owner")
        legacy_first_context = context("2025-06-18", "legacy-1", "legacy-owner")
        legacy_first = await bind(legacy_first_context, "/client/workspace/legacy")
        async with request_context_scope(
            context("2025-06-18", "legacy-2", "legacy-owner"), allow_pwd_bootstrap=False
        ) as legacy_same_context:
            legacy_same = legacy_same_context.session

        assert modern_same is modern_first
        assert modern_other is not modern_first
        assert legacy_same is legacy_first
        assert legacy_first is not modern_first
        assert modern_first.task_manager is not modern_other.task_manager

    finally:
        await runtime.start()
        await runtime.stop()


@pytest.mark.anyio
async def test_modern_request_without_session_id_does_not_reuse_active_bound_session(tmp_path) -> None:
    """A sessionless modern request stays unbound even in an existing async context."""
    from mcp_guide.session import request_context_scope

    runtime = runtime_for_config(tmp_path)
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(
            protocol_version="2026-07-28", request_id="first", meta=None, lifespan_context=runtime
        ),
        session=SimpleNamespace(client_params=None),
        transport="streamable-http",
    )
    try:
        async with request_context_scope(ctx, "bound-owner", allow_pwd_bootstrap=False) as bound_context:
            bound = bound_context.session
            await bound.bind_project_path("/client/workspace/bound-project")
        async with request_context_scope(ctx, allow_pwd_bootstrap=False) as unbound_context:
            unbound = unbound_context.session

        assert unbound is not bound
        assert not unbound.project_is_bound
    finally:
        await bound.cleanup()


@pytest.mark.anyio
async def test_sessionless_modern_request_does_not_register_a_shared_session(tmp_path) -> None:
    """An unbound modern request must not retain a Session in ConfigManager."""
    from mcp_guide.session import request_context_scope

    runtime = runtime_for_config(tmp_path)
    manager = runtime.configuration_service()
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(
            protocol_version="2026-07-28", request_id="unbound", meta=None, lifespan_context=runtime
        ),
        session=SimpleNamespace(client_params=None),
        transport="streamable-http",
    )

    async with request_context_scope(ctx, allow_pwd_bootstrap=False) as request_context:
        assert request_context.session is not None
        assert not request_context.session.project_is_bound

    assert manager._sessions == set()


@pytest.mark.anyio
async def test_concurrent_unbound_requests_with_matching_jsonrpc_ids_are_isolated(tmp_path) -> None:
    """Client-selected JSON-RPC IDs cannot share request-local Session state."""
    from mcp_guide.session import request_context_scope

    runtime = runtime_for_config(tmp_path)

    def context() -> SimpleNamespace:
        return SimpleNamespace(
            request_context=SimpleNamespace(
                protocol_version="2026-07-28", request_id=1, meta=None, lifespan_context=runtime
            ),
            session=SimpleNamespace(client_params=None),
            transport="streamable-http",
        )

    entered = asyncio.Event()
    release = asyncio.Event()

    async def resolve(ctx: SimpleNamespace):
        async with request_context_scope(ctx, allow_pwd_bootstrap=False) as request_context:
            entered.set()
            await release.wait()
            return request_context.session

    first = asyncio.create_task(resolve(context()))
    await entered.wait()
    second = asyncio.create_task(resolve(context()))
    await asyncio.sleep(0)
    release.set()

    first_session, second_session = await asyncio.gather(first, second)

    assert first_session is not second_session


@pytest.mark.anyio
async def test_unbound_request_owners_use_runtime_request_seq(tmp_path) -> None:
    """Concurrent sessionless requests receive distinct unbound:{seq} owners."""
    from mcp_guide.session import request_context_scope

    runtime = runtime_for_config(tmp_path)
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(
            protocol_version="2026-07-28", request_id=1, meta=None, lifespan_context=runtime
        ),
        session=SimpleNamespace(client_params=None),
        transport="streamable-http",
    )

    seqs: list[int] = []
    owners: list[str] = []

    async def capture() -> None:
        async with request_context_scope(ctx, allow_pwd_bootstrap=False) as request_context:
            seqs.append(request_context.seq)
            owners.append(f"unbound:{request_context.seq}")
            assert request_context.session_id is None
            assert runtime.find_session(OwnerKey(f"unbound:{request_context.seq}")) is request_context.session

    await capture()
    await capture()

    assert seqs[0] != seqs[1]
    assert owners[0] != owners[1]
    assert not any(key.value.startswith("unbound:") for key in runtime._sessions)


@pytest.mark.anyio
async def test_stdio_without_pwd_stays_request_local(tmp_path, monkeypatch) -> None:
    """Missing PWD never mints or retains a Session, even on stdio."""
    from unittest.mock import AsyncMock

    import fastmcp.server.sessions as fastmcp_sessions

    import mcp_guide.session as session_module
    from mcp_guide.session import request_context_scope

    class FakeContext:
        def __init__(self, runtime) -> None:
            self.request_context = SimpleNamespace(
                protocol_version="2026-07-28",
                request_id="stdio-no-pwd",
                meta=None,
                lifespan_context=runtime,
            )
            self.session = SimpleNamespace(client_params=None)
            self.session_id = None
            self.transport = "stdio"

    monkeypatch.delenv("PWD", raising=False)
    monkeypatch.delenv("MG_USE_PWD", raising=False)
    runtime = runtime_for_config(tmp_path)
    create_session = AsyncMock(return_value="must-not-mint")
    monkeypatch.setattr(session_module, "Context", FakeContext)
    monkeypatch.setattr(fastmcp_sessions, "create_session", create_session)

    async with request_context_scope(FakeContext(runtime), allow_pwd_bootstrap=True) as request_context:
        assert not request_context.session.project_is_bound
        assert request_context.session_id is None

    create_session.assert_not_awaited()
    assert runtime._sessions == {}
    assert not any(key.value.startswith("unbound:") for key in runtime._sessions)


@pytest.mark.anyio
async def test_stdio_pwd_bootstrap_is_off_by_default(tmp_path, monkeypatch) -> None:
    """Inherited PWD does not bind unless MG_USE_PWD is enabled."""
    from unittest.mock import AsyncMock

    import fastmcp.server.sessions as fastmcp_sessions

    import mcp_guide.session as session_module
    from mcp_guide.session import request_context_scope

    class FakeContext:
        def __init__(self, runtime) -> None:
            self.request_context = SimpleNamespace(
                protocol_version="2026-07-28",
                request_id="stdio-pwd-default-off",
                meta=None,
                lifespan_context=runtime,
            )
            self.session = SimpleNamespace(client_params=None)
            self.session_id = None
            self.transport = "stdio"

    project_root = tmp_path / "stdio-project"
    project_root.mkdir()
    monkeypatch.setenv("PWD", str(project_root))
    monkeypatch.delenv("MG_USE_PWD", raising=False)
    runtime = runtime_for_config(tmp_path)
    create_session = AsyncMock(return_value="must-not-mint")
    monkeypatch.setattr(session_module, "Context", FakeContext)
    monkeypatch.setattr(fastmcp_sessions, "create_session", create_session)

    async with request_context_scope(FakeContext(runtime), allow_pwd_bootstrap=True) as request_context:
        assert not request_context.session.project_is_bound
        assert request_context.session_id is None

    create_session.assert_not_awaited()
    assert runtime._sessions == {}


@pytest.mark.anyio
async def test_modern_stdio_pwd_bootstrap_is_runtime_owned(tmp_path, monkeypatch) -> None:
    """The local PWD shortcut mints a FastMCP session_id and binds that runtime Session."""
    from unittest.mock import AsyncMock

    import fastmcp.server.sessions as fastmcp_sessions

    import mcp_guide.session as session_module
    from mcp_guide.session import request_context_scope

    class FakeContext:
        def __init__(self, runtime) -> None:
            self.request_context = SimpleNamespace(
                protocol_version="2026-07-28",
                request_id="stdio-first",
                meta=None,
                lifespan_context=runtime,
            )
            self.session = SimpleNamespace(client_params=None)
            self.session_id = "stdio-connection"
            self.transport = "stdio"

    project_root = tmp_path / "stdio-project"
    project_root.mkdir()
    monkeypatch.setenv("PWD", str(project_root))
    monkeypatch.setenv("MG_USE_PWD", "1")
    runtime = runtime_for_config(tmp_path / "config")
    create_session = AsyncMock(return_value="minted-stdio-session")
    monkeypatch.setattr(session_module, "Context", FakeContext)
    monkeypatch.setattr(fastmcp_sessions, "create_session", create_session)

    async with request_context_scope(FakeContext(runtime), allow_pwd_bootstrap=True) as request_context:
        session = request_context.session
        assert session.session_id == "minted-stdio-session"
        assert session.bound_root_path == project_root
        create_session.assert_awaited_once()
    assert runtime.find_session(OwnerKey("minted-stdio-session")) is session
    await session.cleanup()


@pytest.mark.anyio
async def test_failed_stdio_pwd_bind_retires_the_minted_session(tmp_path, monkeypatch) -> None:
    """A rejected PWD basename must not leave a minted FastMCP or GuideRuntime Session."""
    from unittest.mock import AsyncMock

    import fastmcp.server.sessions as fastmcp_sessions

    import mcp_guide.session as session_module
    from mcp_guide.session import request_context_scope
    from mcp_guide.validation import InvalidProjectNameError

    class FakeContext:
        def __init__(self, runtime) -> None:
            self.request_context = SimpleNamespace(
                protocol_version="2026-07-28",
                request_id="stdio-bad-pwd",
                meta=None,
                lifespan_context=runtime,
            )
            self.session = SimpleNamespace(client_params=None)
            self.transport = "stdio"

    project_root = tmp_path / "bad name"
    project_root.mkdir()
    monkeypatch.setenv("PWD", str(project_root))
    monkeypatch.setenv("MG_USE_PWD", "1")
    runtime = runtime_for_config(tmp_path / "config")
    create_session = AsyncMock(return_value="minted-then-fail")
    end_session = AsyncMock()
    get_fastmcp_session = AsyncMock(return_value=object())
    monkeypatch.setattr(session_module, "Context", FakeContext)
    monkeypatch.setattr(fastmcp_sessions, "create_session", create_session)
    monkeypatch.setattr(fastmcp_sessions, "end_session", end_session)
    monkeypatch.setattr(fastmcp_sessions, "get_session", get_fastmcp_session)

    with pytest.raises(InvalidProjectNameError):
        async with request_context_scope(FakeContext(runtime), allow_pwd_bootstrap=True):
            pass

    end_session.assert_awaited_once_with("minted-then-fail")
    assert OwnerKey("minted-then-fail") not in runtime._sessions
    assert runtime.configuration_service()._sessions == set()


@pytest.mark.anyio
async def test_non_context_stdio_pwd_does_not_retain_a_connection_owner(tmp_path, monkeypatch) -> None:
    """PWD bootstrap requires a real FastMCP Context; test doubles must not mint stdio: owners."""
    from mcp_guide.session import request_context_scope

    class FakeContext:
        def __init__(self, runtime) -> None:
            self.request_context = SimpleNamespace(
                protocol_version="2026-07-28",
                request_id="stdio-fallback",
                meta=None,
                lifespan_context=runtime,
            )
            self.session = SimpleNamespace(client_params=None)
            self.session_id = "stdio-connection"
            self.transport = "stdio"

    project_root = tmp_path / "stdio-project"
    project_root.mkdir()
    monkeypatch.setenv("PWD", str(project_root))
    runtime = runtime_for_config(tmp_path)

    async with request_context_scope(FakeContext(runtime), allow_pwd_bootstrap=True) as request_context:
        session = request_context.session
        assert OwnerKey("stdio:stdio-connection") not in runtime._sessions
    assert OwnerKey("stdio:stdio-connection") not in runtime._sessions
    assert not any(key.value.startswith("unbound:") for key in runtime._sessions)
    await session.cleanup()


@pytest.mark.anyio
async def test_explicit_session_id_is_validated_for_handshake_era(tmp_path, monkeypatch) -> None:
    """An explicit session_id is FastMCP-validated regardless of protocol era."""
    from unittest.mock import AsyncMock

    import fastmcp.server.sessions as fastmcp_sessions
    from fastmcp.server.sessions import InvalidSession

    import mcp_guide.session as session_module
    from mcp_guide.session import InvalidGuideSessionError, request_context_scope

    class FakeContext:
        def __init__(self, runtime) -> None:
            self.request_context = SimpleNamespace(
                protocol_version="2025-06-18",
                request_id="legacy-explicit",
                meta=None,
                lifespan_context=runtime,
            )
            self.session = SimpleNamespace(client_params=None)
            self.session_id = "connection-id"
            self.transport = "stdio"

    runtime = runtime_for_config(tmp_path)
    monkeypatch.setattr(session_module, "Context", FakeContext)
    get_fastmcp_session = AsyncMock(side_effect=InvalidSession("unknown"))
    monkeypatch.setattr(fastmcp_sessions, "get_session", get_fastmcp_session)

    with pytest.raises(InvalidGuideSessionError):
        async with request_context_scope(FakeContext(runtime), session_id="forged-id", allow_pwd_bootstrap=False):
            pass

    get_fastmcp_session.assert_awaited_once_with("forged-id")


@pytest.mark.anyio
@pytest.mark.parametrize("session_id", ["bad\x00id", "x" * 513])
async def test_malformed_session_id_becomes_invalid_guide_session(tmp_path, session_id) -> None:
    """Control characters and over-length ids are InvalidGuideSessionError, not ValueError."""
    from mcp_guide.session import InvalidGuideSessionError, request_context_scope

    runtime = runtime_for_config(tmp_path)
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(
            protocol_version="2026-07-28",
            request_id="malformed",
            meta=None,
            lifespan_context=runtime,
        ),
        session=SimpleNamespace(client_params=None),
        transport="stdio",
    )
    with pytest.raises(InvalidGuideSessionError):
        async with request_context_scope(ctx, session_id=session_id, allow_pwd_bootstrap=True):
            pass


@pytest.mark.anyio
async def test_supplied_session_id_does_not_pwd_bootstrap(tmp_path, monkeypatch) -> None:
    """A client-supplied id never binds from process PWD, even on stdio."""
    from unittest.mock import AsyncMock

    import fastmcp.server.sessions as fastmcp_sessions
    from fastmcp.server.sessions import InvalidSession

    import mcp_guide.session as session_module
    from mcp_guide.session import InvalidGuideSessionError, request_context_scope

    class FakeContext:
        def __init__(self, runtime) -> None:
            self.request_context = SimpleNamespace(
                protocol_version="2026-07-28",
                request_id="supplied-id",
                meta=None,
                lifespan_context=runtime,
            )
            self.session = SimpleNamespace(client_params=None)
            self.session_id = None
            self.transport = "stdio"

    project_root = tmp_path / "stdio-project"
    project_root.mkdir()
    monkeypatch.setenv("PWD", str(project_root))
    runtime = runtime_for_config(tmp_path / "config")
    monkeypatch.setattr(session_module, "Context", FakeContext)
    monkeypatch.setattr(fastmcp_sessions, "get_session", AsyncMock(side_effect=InvalidSession("unknown")))

    with pytest.raises(InvalidGuideSessionError):
        async with request_context_scope(FakeContext(runtime), session_id="unknown-id", allow_pwd_bootstrap=True):
            pass

    assert not any(getattr(session, "project_is_bound", False) for session in runtime._sessions.values())


@pytest.mark.anyio
async def test_handshake_connection_identity_is_not_bearer_validated(tmp_path, monkeypatch) -> None:
    """Echoing the public connection session_id is the defined handshake owner path."""
    from unittest.mock import AsyncMock

    import fastmcp.server.sessions as fastmcp_sessions

    import mcp_guide.session as session_module
    from mcp_guide.session import request_context_scope

    class FakeContext:
        def __init__(self, runtime) -> None:
            self.request_context = SimpleNamespace(
                protocol_version="2025-06-18",
                request_id="legacy-connection",
                meta=None,
                lifespan_context=runtime,
            )
            self.session = SimpleNamespace(client_params=None)
            self.session_id = "connection-id"
            self.transport = "stdio"

    runtime = runtime_for_config(tmp_path)
    monkeypatch.setattr(session_module, "Context", FakeContext)
    get_fastmcp_session = AsyncMock(side_effect=AssertionError("must not consult the modern session store"))
    monkeypatch.setattr(fastmcp_sessions, "get_session", get_fastmcp_session)

    context = FakeContext(runtime)
    async with request_context_scope(context, session_id="connection-id", allow_pwd_bootstrap=False) as request_context:
        assert request_context.session is runtime.get_current_session("connection-id")
        get_fastmcp_session.assert_not_awaited()
    assert runtime.find_session(OwnerKey("connection-id")) is None


@pytest.mark.anyio
async def test_new_root_binding_is_immediately_visible_in_shared_snapshot(tmp_path) -> None:
    """A runtime project write updates the authoritative image before returning."""
    runtime = runtime_for_config(tmp_path)
    await runtime.start()
    session = runtime.resolve_session(OwnerKey("newly-bound-project"))
    try:
        await session.bind_project_path("/client/workspace/newly-bound-project")

        assert session.project_name in {project.name for project in (await session.get_all_projects()).values()}
    finally:
        await session.cleanup()
        await runtime.stop()


@pytest.mark.anyio
async def test_shared_config_manager_publishes_mutations_to_each_bound_session(tmp_path) -> None:
    """One runtime-owned manager immediately refreshes every affected Session."""
    from unittest.mock import AsyncMock

    from mcp_guide.feature_flags.types import FeatureValue

    runtime = runtime_for_config(tmp_path)
    first = runtime.resolve_session(OwnerKey("first"))
    second = runtime.resolve_session(OwnerKey("second"))
    await first.bind_project_path("/client/workspace/shared-project")
    await second.bind_project_path("/client/workspace/shared-project")

    listener = AsyncMock()
    second.add_listener(listener)

    await get_runtime().set_feature_flag("shared_flag", FeatureValue(True))

    listener.on_config_changed.assert_awaited_once_with(second)
    assert (await get_runtime().get_feature_flags())["shared_flag"].to_raw() is True

    await first.cleanup()
    await second.cleanup()


@pytest.mark.anyio
async def test_shared_config_manager_publishes_each_concurrent_write(tmp_path) -> None:
    """Concurrent writes retain separate deltas rather than suppressing one publication."""
    from unittest.mock import AsyncMock

    from mcp_guide.feature_flags.types import FeatureValue

    runtime = runtime_for_config(tmp_path)
    first = runtime.resolve_session(OwnerKey("first"))
    second = runtime.resolve_session(OwnerKey("second"))
    await first.bind_project_path("/client/workspace/concurrent-project")
    await second.bind_project_path("/client/workspace/concurrent-project")
    listener = AsyncMock()
    second.add_listener(listener)

    await __import__("asyncio").gather(
        get_runtime().set_feature_flag("first_flag", FeatureValue(True)),
        get_runtime().set_feature_flag("second_flag", FeatureValue(True)),
    )

    flags = await get_runtime().get_feature_flags()
    assert flags["first_flag"].to_raw() is True
    assert flags["second_flag"].to_raw() is True
    assert listener.on_config_changed.await_count >= 2
    await first.cleanup()
    await second.cleanup()


@pytest.mark.anyio
async def test_config_watcher_suppresses_its_already_published_snapshot(tmp_path) -> None:
    """The watcher must not repeat a publication for the runtime's own write."""
    from unittest.mock import AsyncMock

    from mcp_guide.feature_flags.types import FeatureValue

    runtime = runtime_for_config(tmp_path)
    manager = runtime.configuration_service()
    session = runtime.resolve_session(OwnerKey("deduplicated-project"))
    await session.bind_project_path("/client/workspace/deduplicated-project")
    listener = AsyncMock()
    session.add_listener(listener)

    await get_runtime().set_feature_flag("shared_flag", FeatureValue(True))
    listener.on_config_changed.assert_awaited_once_with(session)

    await manager._on_external_change(str(manager.config_file))
    listener.on_config_changed.assert_awaited_once_with(session)

    await session.cleanup()


@pytest.mark.anyio
async def test_project_publication_only_refreshes_matching_configuration_identity(tmp_path) -> None:
    """A project write does not restart task state in unrelated Sessions."""
    from dataclasses import replace
    from unittest.mock import AsyncMock

    from mcp_guide.models import Category

    runtime = runtime_for_config(tmp_path)
    first = runtime.resolve_session(OwnerKey("first"))
    matching = runtime.resolve_session(OwnerKey("matching"))
    unrelated = runtime.resolve_session(OwnerKey("unrelated"))
    await first.bind_project_path("/client/workspace/shared-project")
    await matching.bind_project_path("/client/workspace/shared-project")
    await unrelated.bind_project_path("/client/workspace/other-project")

    matching_listener = AsyncMock()
    unrelated_listener = AsyncMock()
    matching.add_listener(matching_listener)
    unrelated.add_listener(unrelated_listener)

    await first.update_config(
        lambda project: replace(project, categories={"api": Category(name="api", dir="src", patterns=["*.py"])})
    )

    matching_listener.on_config_changed.assert_awaited_once_with(matching)
    unrelated_listener.on_config_changed.assert_not_awaited()
    assert "api" in (await matching.get_project()).categories

    await first.cleanup()
    await matching.cleanup()
    await unrelated.cleanup()


@pytest.mark.anyio
async def test_metadata_cache_updates_the_explicit_session_not_ambient_state(tmp_path) -> None:
    """Request adaptation never selects a Session through active-session state."""
    from mcp_guide.mcp_context import cache_mcp_globals

    runtime = runtime_for_config(tmp_path)
    session = runtime.resolve_session(OwnerKey("metadata"))
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(
            meta={"io.modelcontextprotocol/clientInfo": {"name": "Cursor", "version": "1.0"}}
        ),
        session=SimpleNamespace(client_params=None),
    )

    assert await cache_mcp_globals(ctx, session)

    assert session.client_params == {"clientInfo": {"name": "Cursor", "version": "1.0"}}
    await session.cleanup()


@pytest.mark.anyio
async def test_concurrent_bound_request_contexts_keep_separate_projects(tmp_path) -> None:
    """Nested work on two RequestContexts retains each Session and Project pair."""
    runtime = runtime_for_config(tmp_path)
    first = runtime.resolve_session(OwnerKey("first"))
    second = runtime.resolve_session(OwnerKey("second"))
    await first.bind_project_path("/client/workspace/first")
    await second.bind_project_path("/client/workspace/second")
    first_context = await request_context_for(first, "first")
    second_context = await request_context_for(second, "second")

    async def nested(request_context: RequestContext):
        await asyncio.sleep(0)
        return request_context.session, request_context.project

    (first_session, first_project), (second_session, second_project) = await asyncio.gather(
        nested(first_context),
        nested(second_context),
    )

    assert first_session is first
    assert second_session is second
    assert first_project is not second_project
    assert first_project is not None and first_project.name == "first"
    assert second_project is not None and second_project.name == "second"
    await first.cleanup()
    await second.cleanup()
