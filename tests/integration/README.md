# Integration Tests

Integration tests verify that tools are properly registered with the MCP server and work through the MCP protocol.

## The Problem: Tool Registration and Module Caching

**Critical**: Tools are registered with the MCP server via decorators that execute **ON MODULE IMPORT**.

When pytest runs multiple test modules, Python's import system caches modules and does NOT re-import them. This causes contamination:

1. First test module imports `tool_category` → decorators register with ToolsProxy
2. Second test module creates new server → but `tool_category` already cached
3. Tools still registered with OLD server instance
4. Tests fail with signature mismatches

## The Solution: mcp_server_factory Fixture

The `mcp_server_factory` fixture in `conftest.py` solves this by:
1. Resetting the ToolsProxy singleton
2. Creating a fresh server instance
3. Reloading specified tool modules to re-execute decorators
4. Cleaning up after tests complete

## Usage Pattern

```python
@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory):
    """Create fresh MCP server for this test module."""
    return mcp_server_factory(["tool_category", "tool_collection"])


@pytest.mark.anyio
async def test_something(mcp_server):
    """Test via MCP client."""
    async with create_connected_server_and_client_session(mcp_server) as client:
        result = await client.call_tool("category_add", {...})
        # Assert on result...
```

## What to Test Here

Integration tests should ONLY verify:
- Tool is registered with MCP server
- Tool works through MCP protocol (optional, usually covered by unit tests)

**Do NOT test tool logic here** - that belongs in unit tests (`tests/unit/`).

## Unit Tests vs Integration Tests

| Aspect | Unit Tests | Integration Tests |
|--------|-----------|-------------------|
| Location | `tests/unit/` | `tests/integration/` |
| Purpose | Test tool logic | Test MCP registration |
| Function calls | Direct: `await tool(args)` | Via MCP client |
| Fixture needed | No `mcp_server` | Yes, `mcp_server_factory` |
| Speed | Fast | Slower |
| Coverage | 99% of tests | Minimal, registration only |

See `docs/testing-tools.md` for comprehensive testing guide.
