"""Tests for deferred tool registration."""

import pytest

from mcp_guide.core.tool_decorator import _TOOL_REGISTRY, register_tools, toolfunc


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear tool registry before each test."""
    _TOOL_REGISTRY.clear()
    yield
    _TOOL_REGISTRY.clear()


def test_toolfunc_stores_metadata():
    """Test that @toolfunc() stores tool metadata without registering."""

    @toolfunc()
    async def test_tool(ctx=None) -> str:
        return '{"success": true}'

    # Tool should be in registry with prefix
    assert "guide_test_tool" in _TOOL_REGISTRY
    registration = _TOOL_REGISTRY["guide_test_tool"]
    assert registration.metadata.name == "guide_test_tool"
    assert not registration.registered


def test_register_tools_is_idempotent(mock_mcp):
    """Test that register_tools() can be called multiple times safely."""

    @toolfunc()
    async def test_tool(ctx=None) -> str:
        return '{"success": true}'

    # First registration
    register_tools(mock_mcp)
    assert _TOOL_REGISTRY["guide_test_tool"].registered

    # Second registration should be safe
    register_tools(mock_mcp)
    assert _TOOL_REGISTRY["guide_test_tool"].registered

    # MCP.tool should only be called once
    assert mock_mcp.tool_call_count == 1


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
