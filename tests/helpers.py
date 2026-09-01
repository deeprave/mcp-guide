"""Shared test helpers."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastmcp.client.client import CallToolResult
from fastmcp.tools.base import ToolResult

from mcp_guide.runtime import GuideRuntime, OwnerKey

if TYPE_CHECKING:
    from mcp_guide.session import Session


def tool_result_payload(result: ToolResult | CallToolResult) -> dict[str, Any]:
    """Return the structured Guide payload from a native tool response."""
    assert isinstance(result.structured_content, dict)
    return result.structured_content


def create_test_runtime(config_dir: str) -> "GuideRuntime[Session]":
    """Create an isolated runtime that owns its configuration service."""
    from mcp_guide.session import Session

    runtime: GuideRuntime[Session]
    runtime = GuideRuntime(lambda _owner: Session(runtime), config_dir=config_dir)
    return runtime


def create_unbound_test_session(config_dir: str) -> "Session":
    """Create an isolated, runtime-owned Session without binding a project."""
    return create_test_runtime(config_dir).resolve_session(OwnerKey("test-session"))


async def create_bound_test_session(project_name: str, *, _config_dir_for_tests: str) -> "Session":
    """Create a session bound directly to a project for fast test setup."""

    runtime = create_test_runtime(_config_dir_for_tests)
    session = runtime.resolve_session(OwnerKey("test-session"))
    project_root = Path(_config_dir_for_tests) / "client-roots" / project_name
    project_root.mkdir(parents=True, exist_ok=True)
    await session.bind_project_path(project_root)
    return session


async def create_test_session(project_name: str, *, _config_dir_for_tests: str) -> "Session":
    """Create a Session through the explicit client-root binding path."""

    runtime = create_test_runtime(_config_dir_for_tests)
    session = runtime.resolve_session(OwnerKey("test-session"))
    project_root = Path(_config_dir_for_tests) / "client-roots" / project_name
    project_root.mkdir(parents=True, exist_ok=True)
    await session.bind_project_path(project_root)
    return session
