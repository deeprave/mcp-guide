# Refactoring: SSE → Streamable HTTP

## Rationale

**SSE transport is deprecated** in the MCP specification (version 2025-03-26) and replaced by **Streamable HTTP**.

### Why Streamable HTTP?

1. **Single endpoint** - All communication through one endpoint (e.g., `/mcp`)
2. **Simpler architecture** - No separate SSE connection + POST message endpoints
3. **Better compatibility** - Works with standard HTTP infrastructure
4. **MCP standard** - Current specification, not deprecated
5. **FastMCP support** - Built-in via `streamable_http_app()`

### SSE Problems (Deprecated)

- Required two endpoints: `/sse` for server→client, `/messages` for client→server
- Long-lived stateful connections
- Complex session management
- Not all hosting platforms support SSE
- Deprecated in favor of Streamable HTTP

## Implementation Approach

### Extend Existing HTTP Transport

Instead of a new transport, add streaming capability to existing `HttpTransport`:

```python
HttpTransport(
    scheme="http",
    host="localhost",
    port=8080,
    mcp_server=mcp,
    ssl_certfile=None,
    ssl_keyfile=None,
    streaming=True  # NEW: Enable Streamable HTTP
)
```

### CLI Interface

```bash
# Basic HTTP (current)
mcp-guide http

# Streamable HTTP (new)
mcp-guide http --streaming

# Streamable HTTPS with SSL (new)
mcp-guide https --streaming --ssl-certfile cert.pem --ssl-keyfile key.pem

# Custom endpoint path (new)
mcp-guide http://localhost:8080/mcp --streaming
```

### Technical Details

- **No new dependencies** - Reuses existing `[http]` extra with uvicorn
- **FastMCP integration** - Uses `mcp.streamable_http_app()` when streaming enabled
- **Backward compatible** - Basic HTTP unchanged when streaming disabled
- **Single endpoint** - Default `/mcp` path for all communication
- **SSL support** - Works with existing SSL configuration

## Changes Made

1. **Renamed change**: `add-transport-sse` → `add-streamable-http`
2. **Updated proposal**: Focus on Streamable HTTP, not SSE
3. **Updated tasks**: 24 tasks for extending HTTP transport
4. **Updated specs**: Requirements for streaming mode, single endpoint, backward compatibility
5. **Validated**: OpenSpec validation passes

## Next Steps

1. Discuss implementation details
2. Create implementation plan
3. Implement streaming flag and FastMCP integration
4. Test with streaming clients
5. Document usage and examples
