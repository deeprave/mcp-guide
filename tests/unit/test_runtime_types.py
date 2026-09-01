"""Framework-neutral runtime type contracts."""

import asyncio
from types import SimpleNamespace

import pytest

from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.mcp_context import request_context_from_fastmcp, runtime_from_fastmcp
from mcp_guide.models import Project
from mcp_guide.runtime import (
    ClientMetadata,
    GuideRuntime,
    OwnerKey,
    RequestContext,
    RootIdentity,
)
from mcp_guide.utils.project_hash import calculate_project_hash


def runtime_for_config(config_dir):
    """Create a runtime that owns configuration for ``config_dir``."""
    from tests.helpers import create_test_runtime

    return create_test_runtime(str(config_dir))


def test_request_context_carries_the_active_project() -> None:
    """Request context carries the exact immutable active Project."""
    root = RootIdentity.from_path("/client/workspace/demo")
    project = Project(name="review", key=f"review-{root.hash[:8]}", hash=root.hash)
    session = object()

    context = RequestContext(
        protocol_revision="2026-07-28",
        request_id="request-42",
        owner=OwnerKey("agent-42"),
        client=ClientMetadata(name="Cursor", version="1.0"),
        root=root,
        project=project,
        session=session,
    )

    assert context.root == root
    assert context.project is project
    assert context.project.hash == calculate_project_hash("/client/workspace/demo")
    assert context.session is session


def test_request_context_records_the_fastmcp_session_id_when_supplied() -> None:
    """The adapter can retain an explicit FastMCP session ID without an SDK object."""
    context = RequestContext(
        protocol_revision="2026-07-28",
        request_id="request-43",
        owner=OwnerKey("fastmcp:session-43"),
        client=ClientMetadata(),
        session_id="session-43",
        session_source="explicit",
    )

    assert context.session_id == "session-43"
    assert context.session_source == "explicit"


@pytest.mark.parametrize("session_id", ["", "session\n43", "session\x0043", "x" * 513])
def test_request_context_rejects_unsafe_session_ids(session_id: str) -> None:
    """Session identifiers are unstructured but safe for registry use and logging."""
    with pytest.raises(ValueError, match="session ID"):
        RequestContext(
            protocol_revision="2026-07-28",
            request_id="request-44",
            owner=OwnerKey("untrusted-owner"),
            client=ClientMetadata(),
            session_id=session_id,
            session_source="explicit",
        )


def test_root_identity_rejects_relative_client_path() -> None:
    """A root identity cannot be fabricated from an ambiguous client path."""
    with pytest.raises(ValueError, match="absolute"):
        RootIdentity.from_path("demo")


def test_runtime_resolves_sessions_by_explicit_owner() -> None:
    """The global runtime owns a registry instead of using MCP connection objects."""
    created: list[object] = []

    def create_session(_owner: OwnerKey) -> object:
        session = object()
        created.append(session)
        return session

    runtime = GuideRuntime(session_factory=create_session)

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

    runtime = GuideRuntime(lambda _owner: object(), on_start=on_start, on_stop=on_stop)
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
    runtime = GuideRuntime(lambda _owner: object(), config_dir=str(tmp_path))

    await runtime.start()
    assert await runtime.get_docroot() == "/configured/docs"
    await runtime.stop()


def test_session_obtains_its_configuration_service_from_its_runtime(tmp_path) -> None:
    """Session keeps only its runtime, not a duplicate configuration reference."""
    from mcp_guide.session import Session

    runtime: GuideRuntime[Session]

    def create_session(_owner: OwnerKey) -> Session:
        return Session(runtime)

    runtime = GuideRuntime(create_session, config_dir=str(tmp_path))
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

    runtime = GuideRuntime(lambda _owner: TestSession())
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
    runtime = GuideRuntime(lambda _owner: sessions.pop(0), config_dir=str(tmp_path))
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

    runtime = GuideRuntime(lambda _owner: TestSession(), session_idle_timeout=10)
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

    runtime = GuideRuntime(lambda _owner: TestSession())
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

    runtime = GuideRuntime(lambda _owner: SessionWithCleanup(), session_idle_timeout=1)
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
    runtime = GuideRuntime(lambda _owner: object())

    async with runtime.lifespan() as lifespan_context:
        assert lifespan_context is runtime
        assert runtime.started

    assert not runtime.started


def test_request_adapter_uses_explicit_id_for_modern_request() -> None:
    """Modern state is keyed only by the explicit, validated tool argument."""
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(
            protocol_version="2026-07-28",
            request_id="request-45",
            meta={"io.modelcontextprotocol/clientInfo": {"name": "Cursor", "version": "1.0"}},
        ),
        session=SimpleNamespace(client_params=None),
    )

    context = request_context_from_fastmcp(ctx, session_id="fastmcp-session-45")

    assert context.owner == OwnerKey("fastmcp-session-45")
    assert context.session_source == "explicit"
    assert context.client == ClientMetadata(name="Cursor", version="1.0")


def test_request_adapter_does_not_make_modern_state_without_an_explicit_id() -> None:
    """A modern request without session state remains unbound for this request."""
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(protocol_version="2026-07-28", request_id="request-46", meta=None),
        session=SimpleNamespace(client_params=None),
    )

    context = request_context_from_fastmcp(ctx)

    assert context.session_id is None
    assert context.session_source is None
    assert context.owner.value.startswith("unbound:")
    assert context.owner != OwnerKey("unbound:request-46")


def test_request_adapter_uses_public_legacy_connection_id() -> None:
    """Retained handshake clients retain their public FastMCP connection identity."""
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(protocol_version="2025-06-18", request_id="request-47", meta=None),
        session_id="legacy-session-47",
        session=SimpleNamespace(client_params={"clientInfo": {"name": "Legacy", "version": "2.0"}}),
    )

    context = request_context_from_fastmcp(ctx)

    assert context.owner == OwnerKey("legacy-session-47")
    assert context.session_source == "legacy"
    assert context.client == ClientMetadata(name="Legacy", version="2.0")


def test_all_tool_arguments_advertise_an_optional_session_id() -> None:
    """The session identifier is a standard tool fixture, not per-tool boilerplate."""
    schema = ToolArguments.model_json_schema()

    assert "session_id" in schema["properties"]
    assert "session_id" not in schema.get("required", [])


def test_runtime_adapter_reads_the_public_lifespan_context() -> None:
    """Request handling obtains its runtime from FastMCP, not a module singleton."""
    runtime = GuideRuntime(lambda _owner: object())
    ctx = SimpleNamespace(request_context=SimpleNamespace(lifespan_context=runtime))

    assert runtime_from_fastmcp(ctx) is runtime


@pytest.mark.anyio
async def test_runtime_session_resolution_isolated_by_modern_and_legacy_owner(tmp_path) -> None:
    """Bound modern and legacy owners resolve isolated runtime Sessions."""
    from mcp_guide.session import Session, get_session, set_project

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

    try:
        modern_first_context = context("2026-07-28", "modern-1")
        assert (await set_project("/client/workspace/modern", modern_first_context, session_id="modern-owner")).is_ok()
        modern_first = await get_session(modern_first_context, session_id="modern-owner")
        modern_same = await get_session(context("2026-07-28", "modern-2"), session_id="modern-owner")
        modern_other_context = context("2026-07-28", "modern-3")
        assert (await set_project("/client/workspace/other", modern_other_context, session_id="other-owner")).is_ok()
        modern_other = await get_session(modern_other_context, session_id="other-owner")
        legacy_first_context = context("2025-06-18", "legacy-1", "legacy-owner")
        assert (await set_project("/client/workspace/legacy", legacy_first_context)).is_ok()
        legacy_first = await get_session(legacy_first_context)
        legacy_same = await get_session(context("2025-06-18", "legacy-2", "legacy-owner"))

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
    from mcp_guide.session import get_session

    runtime = runtime_for_config(tmp_path)
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(
            protocol_version="2026-07-28", request_id="first", meta=None, lifespan_context=runtime
        ),
        session=SimpleNamespace(client_params=None),
        transport="streamable-http",
    )
    try:
        bound = await get_session(ctx, session_id="bound-owner")
        await bound.bind_project_path("/client/workspace/bound-project")
        unbound = await get_session(ctx)

        assert unbound is not bound
        assert not unbound.project_is_bound
    finally:
        await bound.cleanup()


@pytest.mark.anyio
async def test_sessionless_modern_request_does_not_register_a_shared_session(tmp_path) -> None:
    """An unbound modern request must not retain a Session in ConfigManager."""
    from mcp_guide.session import request_session_scope

    runtime = runtime_for_config(tmp_path)
    manager = runtime.configuration_service()
    ctx = SimpleNamespace(
        request_context=SimpleNamespace(
            protocol_version="2026-07-28", request_id="unbound", meta=None, lifespan_context=runtime
        ),
        session=SimpleNamespace(client_params=None),
        transport="streamable-http",
    )

    async with request_session_scope(ctx) as session:
        assert session is not None
        assert not session.project_is_bound

    assert manager._sessions == set()


@pytest.mark.anyio
async def test_concurrent_unbound_requests_with_matching_jsonrpc_ids_are_isolated(tmp_path) -> None:
    """Client-selected JSON-RPC IDs cannot share request-local Session state."""
    from mcp_guide.session import request_session_scope

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
        async with request_session_scope(ctx) as session:
            entered.set()
            await release.wait()
            return session

    first = asyncio.create_task(resolve(context()))
    await entered.wait()
    second = asyncio.create_task(resolve(context()))
    await asyncio.sleep(0)
    release.set()

    first_session, second_session = await asyncio.gather(first, second)

    assert first_session is not second_session


@pytest.mark.anyio
async def test_modern_stdio_pwd_bootstrap_is_runtime_owned(tmp_path, monkeypatch) -> None:
    """The local PWD shortcut mints a FastMCP session_id and binds that runtime Session."""
    from unittest.mock import AsyncMock

    import fastmcp.server.sessions as fastmcp_sessions

    import mcp_guide.session as session_module
    from mcp_guide.session import get_session

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
    runtime = runtime_for_config(tmp_path / "config")
    create_session = AsyncMock(return_value="minted-stdio-session")
    get_fastmcp_session = AsyncMock(return_value=object())
    monkeypatch.setattr(session_module, "Context", FakeContext)
    monkeypatch.setattr(fastmcp_sessions, "create_session", create_session)
    monkeypatch.setattr(fastmcp_sessions, "get_session", get_fastmcp_session)

    session = await get_session(FakeContext(runtime))
    try:
        assert session is runtime.resolve_session(OwnerKey("minted-stdio-session"))
        assert session.bound_root_path == project_root
        assert session.session_id == "minted-stdio-session"
        create_session.assert_awaited_once()
        get_fastmcp_session.assert_awaited()
    finally:
        await session.cleanup()


@pytest.mark.anyio
async def test_failed_stdio_pwd_bind_retires_the_minted_session(tmp_path, monkeypatch) -> None:
    """A rejected PWD basename must not leave a minted FastMCP or GuideRuntime Session."""
    from unittest.mock import AsyncMock

    import fastmcp.server.sessions as fastmcp_sessions

    import mcp_guide.session as session_module
    from mcp_guide.session import get_session
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
    runtime = runtime_for_config(tmp_path / "config")
    create_session = AsyncMock(return_value="minted-then-fail")
    end_session = AsyncMock()
    get_fastmcp_session = AsyncMock(return_value=object())
    monkeypatch.setattr(session_module, "Context", FakeContext)
    monkeypatch.setattr(fastmcp_sessions, "create_session", create_session)
    monkeypatch.setattr(fastmcp_sessions, "end_session", end_session)
    monkeypatch.setattr(fastmcp_sessions, "get_session", get_fastmcp_session)

    with pytest.raises(InvalidProjectNameError):
        await get_session(FakeContext(runtime))

    end_session.assert_awaited_once_with("minted-then-fail")
    assert OwnerKey("minted-then-fail") not in runtime._sessions
    assert runtime.configuration_service()._sessions == set()


@pytest.mark.anyio
async def test_failed_fallback_stdio_pwd_discards_the_connection_owner(tmp_path, monkeypatch) -> None:
    """A skipped mint must not leave a stdio:{connection} Session after a failed bind."""
    from unittest.mock import AsyncMock

    import fastmcp.server.sessions as fastmcp_sessions

    from mcp_guide.session import get_session
    from mcp_guide.validation import InvalidProjectNameError

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

    project_root = tmp_path / "bad name"
    project_root.mkdir()
    monkeypatch.setenv("PWD", str(project_root))
    runtime = runtime_for_config(tmp_path / "config")
    end_session = AsyncMock()
    monkeypatch.setattr(fastmcp_sessions, "end_session", end_session)

    with pytest.raises(InvalidProjectNameError):
        await get_session(FakeContext(runtime))

    end_session.assert_not_awaited()
    assert OwnerKey("stdio:stdio-connection") not in runtime._sessions


@pytest.mark.anyio
async def test_explicit_session_id_is_validated_for_handshake_era(tmp_path, monkeypatch) -> None:
    """An explicit session_id is FastMCP-validated regardless of protocol era."""
    from unittest.mock import AsyncMock

    import fastmcp.server.sessions as fastmcp_sessions
    from fastmcp.server.sessions import InvalidSession

    import mcp_guide.session as session_module
    from mcp_guide.session import InvalidGuideSessionError, get_session

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
        await get_session(FakeContext(runtime), session_id="forged-id")

    get_fastmcp_session.assert_awaited_once_with("forged-id")


@pytest.mark.anyio
async def test_handshake_connection_identity_is_not_bearer_validated(tmp_path, monkeypatch) -> None:
    """Echoing the public connection session_id is the defined handshake owner path."""
    from unittest.mock import AsyncMock

    import fastmcp.server.sessions as fastmcp_sessions

    import mcp_guide.session as session_module
    from mcp_guide.session import get_session, request_session_scope

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
    async with request_session_scope(context, session_id="connection-id") as session:
        assert session is await get_session(context, session_id="connection-id")
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

    await first.runtime.set_feature_flag("shared_flag", FeatureValue(True))

    listener.on_config_changed.assert_awaited_once_with(second)
    assert (await second.runtime.get_feature_flags())["shared_flag"].to_raw() is True

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
        first.runtime.set_feature_flag("first_flag", FeatureValue(True)),
        second.runtime.set_feature_flag("second_flag", FeatureValue(True)),
    )

    flags = await first.runtime.get_feature_flags()
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

    await session.runtime.set_feature_flag("shared_flag", FeatureValue(True))
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
