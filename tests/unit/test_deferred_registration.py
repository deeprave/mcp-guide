"""Tests for deferred tool registration."""

import pytest

from mcp_guide.core.tool_decorator import (
    clear_tool_registry,
    get_tool_registration,
    get_tool_registry,
    register_tools,
    toolfunc,
)


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear tool registry before each test."""
    clear_tool_registry()
    yield
    clear_tool_registry()


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
