"""Tests for deferred tool registration."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp.tools.base import ToolResult
from tests.helpers import create_test_runtime

from mcp_guide.core.tool_decorator import (
    clear_tool_registry,
    get_tool_registration,
    get_tool_registry,
    register_tools,
    toolfunc,
)
from mcp_guide.result import Result


def request_context(tmp_path):
    """Build the FastMCP-facing test input for a public tool boundary."""
    runtime = create_test_runtime(str(tmp_path))
    return SimpleNamespace(
        request_context=SimpleNamespace(
            protocol_version="2026-07-28", request_id="deferred-tool", meta=None, lifespan_context=runtime
        ),
        session=SimpleNamespace(client_params=None),
        transport="streamable-http",
    )


@pytest.fixture(autouse=True)
def clear_registry():
    """Isolate registrations without erasing the imported production surface."""
    import mcp_guide.tools  # noqa: F401
    from mcp_guide.core import tool_decorator

    original_registry = deepcopy(tool_decorator._TOOL_REGISTRY)
    clear_tool_registry()
    yield
    clear_tool_registry()
    tool_decorator._TOOL_REGISTRY.update(original_registry)


def test_toolfunc_requires_an_args_class() -> None:
    """Every tool carries session_id, so the no-args wrapper is not available."""
    with pytest.raises(TypeError, match="args_class"):
        toolfunc()  # type: ignore[call-arg]


def test_toolfunc_stores_metadata():
    """Test that @toolfunc stores tool metadata without registering."""

    @toolfunc(object)
    async def test_tool(args, request_context) -> str:
        return '{"success": true}'

    # Tool should be in registry without prefix (default is empty)
    assert "test_tool" in get_tool_registry()
    registration = get_tool_registration("test_tool")
    assert registration.metadata.name == "test_tool"
    assert registration.metadata.args_class is object
    assert not registration.registered


def test_register_tools_is_idempotent(mock_mcp):
    """Test that register_tools() can be called multiple times safely."""

    @toolfunc(object)
    async def test_tool(args, request_context) -> str:
        return '{"success": true}'

    # First registration
    register_tools(mock_mcp)
    first_count = mock_mcp.tool_call_count
    assert first_count > 0
    assert get_tool_registration("test_tool").registered

    # Second registration should be idempotent - no new registrations
    register_tools(mock_mcp)
    assert mock_mcp.tool_call_count == first_count


@pytest.mark.anyio
async def test_project_binding_tool_does_not_allocate_pre_binding_session(tmp_path):
    """A binding tool must mint its FastMCP ID before task interception runs."""

    @toolfunc(args_class=object, requires_project=False, binds_project=True)
    async def bind_project(args, request_context):
        return Result.ok("bound")

    wrapper = get_tool_registration("bind_project").metadata.wrapped_func
    with patch("mcp_guide.core.tool_decorator._call_on_tool", new=AsyncMock()) as on_tool:
        output = await wrapper(object(), ctx=request_context(tmp_path))

    on_tool.assert_not_awaited()
    assert isinstance(output, ToolResult)
    assert output.structured_content["value"] == "bound"


@pytest.mark.anyio
async def test_unmintable_binding_tool_returns_project_error(tmp_path, monkeypatch):
    """A binding tool maps an unmintable session to an in-band Guide result."""
    import mcp_guide.session as session_module

    class FakeContext:
        def __init__(self, runtime) -> None:
            self.request_context = SimpleNamespace(
                protocol_version="legacy",
                request_id="unmintable-bind",
                meta=None,
                lifespan_context=runtime,
            )
            self.session = SimpleNamespace(client_params=None)
            self.session_id = None
            self.transport = "streamable-http"

    runtime = create_test_runtime(str(tmp_path))
    monkeypatch.setattr(session_module, "Context", FakeContext)

    @toolfunc(args_class=object, requires_project=False, binds_project=True)
    async def bind_project(args, request_context):
        return Result.ok("must-not-run")

    wrapper = get_tool_registration("bind_project").metadata.wrapped_func
    output = await wrapper(object(), ctx=FakeContext(runtime))

    assert isinstance(output, ToolResult)
    assert output.is_error
    assert output.structured_content["error_type"] == "project_error"
    assert "cannot carry a Guide session" in output.structured_content["error"]
    assert "2026-07-28" in output.structured_content["instruction"]


@pytest.mark.anyio
async def test_deferred_tool_adapts_an_internal_result_to_native_fastmcp_response(tmp_path):
    """Migrated tools can return Result without adopting a second boundary."""

    @toolfunc(args_class=object, requires_project=False)
    async def raw_result(args, request_context):
        return Result.ok("native boundary")

    wrapper = get_tool_registration("raw_result").metadata.wrapped_func
    output = await wrapper(object(), ctx=request_context(tmp_path))

    assert isinstance(output, ToolResult)
    assert output.structured_content["value"] == "native boundary"
    assert not output.is_error


@pytest.mark.anyio
async def test_deferred_tool_preserves_native_error_status(tmp_path):
    """The decorator must not discard FastMCP's native tool error signal."""

    @toolfunc(args_class=object, requires_project=False)
    async def failed_result(args, request_context):
        return Result.failure("native error")

    wrapper = get_tool_registration("failed_result").metadata.wrapped_func
    output = await wrapper(object(), ctx=request_context(tmp_path))

    assert isinstance(output, ToolResult)
    assert output.is_error
    assert output.structured_content["error"] == "native error"


@pytest.fixture
def mock_mcp():
    """Mock MCP instance for testing."""

    class MockMCP:
        def __init__(self):
            self.tool_call_count = 0
            self.registered_tools = []

        def tool(self, name, description):
            def decorator(func):
                self.tool_call_count += 1
                self.registered_tools.append(name)
                return func

            return decorator

    return MockMCP()
