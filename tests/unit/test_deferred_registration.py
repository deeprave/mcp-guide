"""Tests for deferred tool registration."""

from copy import deepcopy
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp.tools.base import ToolResult

from mcp_guide.core.tool_decorator import (
    clear_tool_registry,
    get_tool_registration,
    get_tool_registry,
    register_tools,
    toolfunc,
)
from mcp_guide.result import Result


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


def test_toolfunc_stores_metadata():
    """Test that @toolfunc() stores tool metadata without registering."""

    @toolfunc()
    async def test_tool(ctx=None) -> str:
        return '{"success": true}'

    # Tool should be in registry without prefix (default is empty)
    assert "test_tool" in get_tool_registry()
    registration = get_tool_registration("test_tool")
    assert registration.metadata.name == "test_tool"
    assert not registration.registered


def test_register_tools_is_idempotent(mock_mcp):
    """Test that register_tools() can be called multiple times safely."""

    @toolfunc()
    async def test_tool(ctx=None) -> str:
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
async def test_project_binding_tool_does_not_allocate_pre_binding_session():
    """A binding tool must mint its FastMCP ID before task interception runs."""

    @toolfunc(args_class=object, requires_project=False, binds_project=True)
    async def bind_project(args, ctx=None):
        return Result.ok("bound")

    wrapper = get_tool_registration("bind_project").metadata.wrapped_func
    with patch("mcp_guide.core.tool_decorator._call_on_tool", new=AsyncMock()) as on_tool:
        output = await wrapper(object())

    on_tool.assert_not_awaited()
    assert isinstance(output, ToolResult)
    assert output.structured_content["value"] == "bound"


@pytest.mark.anyio
async def test_deferred_tool_adapts_an_internal_result_to_native_fastmcp_response():
    """Migrated tools can return Result without adopting a second boundary."""

    @toolfunc(args_class=object, requires_project=False)
    async def raw_result(args, ctx=None):
        return Result.ok("native boundary")

    wrapper = get_tool_registration("raw_result").metadata.wrapped_func
    output = await wrapper(object())

    assert isinstance(output, ToolResult)
    assert output.structured_content["value"] == "native boundary"
    assert not output.is_error


@pytest.mark.anyio
async def test_deferred_tool_preserves_native_error_status():
    """The decorator must not discard FastMCP's native tool error signal."""

    @toolfunc(args_class=object, requires_project=False)
    async def failed_result(args, ctx=None):
        return Result.failure("native error")

    wrapper = get_tool_registration("failed_result").metadata.wrapped_func
    output = await wrapper(object())

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
