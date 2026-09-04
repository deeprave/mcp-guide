"""Shared test helpers."""

import inspect
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastmcp.client.client import CallToolResult
from fastmcp.tools.base import ToolResult

from mcp_guide.runtime import GuideRuntime, OwnerKey, create_runtime

if TYPE_CHECKING:
    from mcp_guide.runtime import RequestContext
    from mcp_guide.session import Session


def tool_result_payload(result: ToolResult | CallToolResult) -> dict[str, Any]:
    """Return the structured Guide payload from a native tool response."""
    assert isinstance(result.structured_content, dict)
    return result.structured_content


def application_runtime(server: Any) -> GuideRuntime[Any]:
    """Return the GuideRuntime closed over by a FastMCP application lifespan."""
    return inspect.getclosurevars(server._lifespan).nonlocals["runtime"]


def runtime_config_dir(runtime: GuideRuntime[Any]) -> Path:
    """Return the isolated configuration directory owned by ``runtime``."""
    return runtime.configuration_service().config_file.parent


async def request_context_for(session: "Session", session_id: str | None = None) -> "RequestContext":
    """Build a RequestContext through the session's runtime factory."""
    runtime = getattr(session, "_runtime", None)
    if not isinstance(runtime, GuideRuntime):
        candidate = getattr(session, "runtime", None)
        runtime = candidate if isinstance(candidate, GuideRuntime) else None
    if runtime is None:
        from mcp_guide.runtime import get_runtime

        runtime = get_runtime()
    seq = runtime.next_request_seq()
    resolved_id = session_id
    if resolved_id is None:
        candidate = getattr(session, "session_id", None)
        resolved_id = candidate if isinstance(candidate, str) else None
    return await runtime.request_context(session, session_id=resolved_id, seq=seq)


def create_test_runtime(config_dir: str, *, docroot: str | Path | None = None) -> "GuideRuntime[Session]":
    """Install the process runtime for tests through create_runtime()."""
    from mcp_guide.session import Session

    runtime: GuideRuntime[Session]
    runtime = create_runtime(lambda _owner: Session(runtime), config_dir=config_dir, docroot=docroot)
    return runtime


def unique_test_project_name(prefix: str = "test") -> str:
    """Return a project name unique to one test interaction."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def create_unbound_test_session(runtime: "GuideRuntime[Session]") -> "Session":
    """Create an isolated, runtime-owned Session without binding a project."""
    return runtime.resolve_session(OwnerKey(f"test-session:{uuid.uuid4().hex}"))


async def bind_isolated_test_session(
    runtime: "GuideRuntime[Session]",
    *,
    project_name: str = "test",
) -> "Session":
    """Bind a new Session using a client root under the runtime config directory."""
    from mcp_guide.session import bind_session_project

    session = create_unbound_test_session(runtime)
    project_root = runtime_config_dir(runtime) / "client-roots" / project_name
    project_root.mkdir(parents=True, exist_ok=True)
    await bind_session_project(session, project_root)
    return session


async def _bind_named_test_session(runtime: "GuideRuntime[Session]", project_name: str) -> "Session":
    """Create a runtime-owned Session and bind it through the production path."""
    from mcp_guide.session import bind_session_project

    session = create_unbound_test_session(runtime)
    project_root = runtime_config_dir(runtime) / "client-roots" / project_name
    project_root.mkdir(parents=True, exist_ok=True)
    await bind_session_project(session, project_root)
    return session


async def create_bound_test_session(runtime: "GuideRuntime[Session]", project_name: str) -> "Session":
    """Create a session bound directly to a project for fast test setup."""
    return await _bind_named_test_session(runtime, project_name)


async def create_test_session(runtime: "GuideRuntime[Session]", project_name: str) -> "Session":
    """Create a Session through the explicit client-root binding path."""
    return await _bind_named_test_session(runtime, project_name)
