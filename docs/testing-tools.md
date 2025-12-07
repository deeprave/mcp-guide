# Testing MCP Tools: Unit vs Integration Tests

## The Problem: Tool Registration and Import Caching

MCP tools are registered with the server via decorators that execute **ON MODULE IMPORT**. Python's import system caches modules, which causes contamination between test modules when running the full test suite.

### What Happens

1. **First test module** imports `tool_category` → decorators register tools with ToolsProxy
2. **Second test module** creates new MCP server → but `tool_category` is already imported and cached
3. Tools from first module are still registered with the **OLD** server instance
4. Direct function calls fail because the decorator wrapper expects a different signature

### The Solution: Separate Unit and Integration Tests

## Unit Tests (Direct Function Calls)

**Location**: `tests/unit/test_mcp_guide/tools/test_tool_*.py`

**Purpose**: Test tool logic in isolation without MCP protocol overhead

**Pattern**:
```python
"""Unit tests for tool_example."""

import json
from pathlib import Path

import pytest

from mcp_guide.config import ConfigManager
from mcp_guide.models import Project
from mcp_guide.session import Session, set_current_session, remove_current_session
from mcp_guide.tools.tool_example import ExampleArgs, example_tool


class TestExampleTool:
    """Tests for example_tool."""

    @pytest.mark.asyncio
    async def test_example_functionality(self, tmp_path: Path, monkeypatch):
        """Test example tool logic."""
        # Set PWD to control project name detection
        monkeypatch.setenv("PWD", "/fake/path/test-project")

        # Create test session
        manager = ConfigManager(config_dir=str(tmp_path))
        session = Session(_config_manager=manager, project_name="test-project")
        session._cached_project = Project(name="test-project", categories=[], collections=[])
        set_current_session(session)

        try:
            # Call tool directly
            args = ExampleArgs(param="value")
            result_str = await example_tool(args)
            result = json.loads(result_str)

            # Assert results
            assert result["success"] is True
            assert result["value"] == "expected"
        finally:
            remove_current_session("test-project")
```

**Key Points**:
- Import tool functions at **module level** (top of file)
- Call functions **directly** with args: `await tool_function(args)`
- No `ctx` parameter needed
- No `mcp_server` fixture needed
- Use `monkeypatch.setenv("PWD", ...)` to control project detection
- Always clean up with `remove_current_session()` in finally block

## Integration Tests (MCP Protocol)

**Location**: `tests/integration/test_tool_*.py`

**Purpose**: Verify tool registration with MCP server

**Pattern**:
```python
"""Integration test for tool_example registration."""

import pytest


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory):
    """Create fresh MCP server for this test module.

    See tests/integration/conftest.py for why this is necessary.
    """
    return mcp_server_factory(["tool_example"])


@pytest.mark.anyio
async def test_example_tool_registered(mcp_server):
    """Test that example_tool is registered in MCP."""
    tools = await mcp_server.list_tools()
    tool_names = [tool.name for tool in tools]

    assert "example_tool" in tool_names
```

**Key Points**:
- Use `mcp_server_factory()` helper to handle module reloading
- Only test **registration**, not functionality
- Functional tests belong in unit tests

## The MCP Server Factory Fixture

**Location**: `tests/integration/conftest.py`

**See `tests/integration/README.md` for detailed usage and explanation.**

Quick example:
```python
@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory):
    return mcp_server_factory(["tool_example"])
```

## Quick Reference

| Test Type | Location | Imports | Function Call | Fixture Needed |
|-----------|----------|---------|---------------|----------------|
| **Unit** | `tests/unit/` | Module level | `await tool(args)` | No `mcp_server` |
| **Integration** | `tests/integration/` | N/A | Via MCP client | Yes, use helper |

## Common Mistakes

### ❌ Wrong: Integration test calling function directly
```python
# tests/integration/test_tool_example.py
async def test_example(mcp_server):
    from mcp_guide.tools.tool_example import example_tool  # ❌ Import in test
    result = await example_tool(args)  # ❌ Direct call
```

**Problem**: Module already imported by other tests, decorator contamination

### ✅ Right: Unit test calling function directly
```python
# tests/unit/test_mcp_guide/tools/test_tool_example.py
from mcp_guide.tools.tool_example import example_tool  # ✅ Module-level import

async def test_example(tmp_path, monkeypatch):
    result = await example_tool(args)  # ✅ Direct call, no mcp_server
```

### ✅ Right: Integration test via MCP client
```python
# tests/integration/test_tool_example.py
async def test_example(mcp_server, test_session, monkeypatch):
    async with create_connected_server_and_client_session(mcp_server) as client:
        result = await client.call_tool("example_tool", {"param": "value"})  # ✅ Via MCP
```

## When to Use Each

**Use Unit Tests** (99% of cases):
- Testing tool logic and behavior
- Testing error handling
- Testing different argument combinations
- Testing edge cases
- Fast execution, no protocol overhead

**Use Integration Tests** (minimal):
- Verifying tool is registered with MCP server
- Testing end-to-end MCP protocol workflows (rare)
- One simple registration test per tool is usually sufficient

## Summary

- **Unit tests**: Direct function calls, no MCP server, test logic
- **Integration tests**: MCP client calls, test registration only
- **Never mix**: Don't call functions directly in integration tests
- **Use the helper**: `mcp_server_factory()` for integration tests
- **Clean up**: Always use `remove_current_session()` in unit tests
