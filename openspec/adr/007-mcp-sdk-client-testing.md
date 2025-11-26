# ADR-007: MCP SDK Client-Based Integration Testing

**Status**: Accepted
**Date**: 2025-11-26
**Deciders**: David Nugent
**Related**: ADR-005 (MCP Inspector for Integration Testing)

## Context

We need a robust approach for integration testing our MCP server that closely simulates real-world usage by MCP clients like Claude Desktop. While basic subprocess-based tests validate the protocol, they don't use the official MCP client implementation and may miss compatibility issues.

The MCP Python SDK provides two approaches for testing:
1. **In-memory testing**: `create_connected_server_and_client_session()` - Direct connection without subprocess
2. **STDIO client testing**: `stdio_client()` with `StdioServerParameters` - Spawns actual server process

Initial investigation of `mcp-inspector` package revealed it's a placeholder (v0.1.0) with no actual implementation. However, the core `mcp` package provides comprehensive client functionality for testing.

## Decision

We will use the **MCP SDK's official client testing utilities** for future comprehensive integration tests:

### Primary Approach: STDIO Client Testing
Use `mcp.client.stdio.stdio_client()` for integration tests that:
- Spawn the actual `mcp-guide` command as a subprocess
- Communicate via STDIO transport (matching production usage)
- Use the official MCP client implementation
- Validate real-world compatibility

### Secondary Approach: In-Memory Testing
Use `mcp.shared.memory.create_connected_server_and_client_session()` for:
- Fast unit-style integration tests
- Testing server logic without subprocess overhead
- Rapid feedback during development

### Current MVP Approach
For the initial implementation, we use simple subprocess-based tests that:
- Validate basic MCP protocol handshake
- Ensure server starts without errors
- Verify server metadata
- Are sufficient for MVP validation

## Rationale

### Why MCP SDK Client Testing?

1. **Official Implementation**: Uses the same client code that Claude Desktop and other MCP clients use
2. **Real-world Validation**: Tests actual compatibility with MCP ecosystem
3. **Comprehensive**: Validates full request/response cycle, not just JSON-RPC
4. **Maintainable**: SDK handles protocol details, we focus on server behavior
5. **Well-documented**: Official MCP SDK testing guide provides patterns

### Why Not Now?

1. **MVP Scope**: Current simple tests are sufficient for initial validation
2. **Incremental Improvement**: Can add comprehensive tests in future iteration
3. **Clear Path Forward**: SDK provides clear testing patterns to follow
4. **No Blocking Issues**: Current tests validate core functionality

### Why Not mcp-inspector?

1. **Placeholder Package**: Current version (0.1.0) has no implementation
2. **SDK Sufficient**: Core `mcp` package provides all needed client functionality
3. **Direct Access**: No need for wrapper when SDK provides the tools

## Implementation Guide

### STDIO Client Testing Pattern

```python
import pytest
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

@pytest.fixture
async def mcp_client():
    """Create MCP client connected to mcp-guide server."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp-guide"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session

@pytest.mark.asyncio
async def test_server_tools(mcp_client):
    """Test server tools using MCP client."""
    tools = await mcp_client.list_tools()
    assert len(tools.tools) > 0
```

### In-Memory Testing Pattern

```python
import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.client.session import ClientSession

@pytest.fixture
async def client_session():
    """Create in-memory client-server session."""
    from mcp_guide.server import create_server

    server = create_server()
    async with create_connected_server_and_client_session(
        server,
        raise_exceptions=True
    ) as session:
        yield session

@pytest.mark.asyncio
async def test_tool_call(client_session: ClientSession):
    """Test tool call via in-memory session."""
    result = await client_session.call_tool("tool_name", {"arg": "value"})
    assert result.content[0].text == "expected"
```

## Consequences

### Positive

- **Future-proof**: Clear path to comprehensive integration testing
- **Ecosystem Compatible**: Tests validate real MCP client compatibility
- **Flexible**: Two approaches for different testing needs
- **Official**: Uses recommended MCP SDK testing patterns
- **Documented**: ADR provides reference for future implementation

### Negative

- **Deferred Work**: Comprehensive tests not implemented in MVP
- **Learning Curve**: Team needs to learn MCP SDK client APIs
- **Dependency**: Relies on MCP SDK stability and compatibility

### Neutral

- **Current Tests Remain**: Simple subprocess tests stay for MVP
- **Incremental Adoption**: Can migrate tests gradually
- **No Breaking Changes**: Existing tests continue to work

## References

- [MCP SDK Testing Guide](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/testing.md)
- [MCP SDK Python Client](https://github.com/modelcontextprotocol/python-sdk)
- ADR-005: MCP Inspector for Integration Testing
- `mcp.client.stdio` module documentation
- `mcp.shared.memory` module documentation

## Future Work

1. **Create pytest fixtures** for MCP client sessions (both STDIO and in-memory)
2. **Add comprehensive tool tests** using MCP client
3. **Add resource tests** using MCP client
4. **Add prompt tests** using MCP client
5. **Consider pytest plugin** for MCP server testing (if patterns emerge)
6. **Performance benchmarks** using in-memory testing for speed
