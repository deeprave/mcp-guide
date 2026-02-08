# Add Streamable HTTP Transport

## Why

The current HTTP transport uses basic request/response pattern. Streamable HTTP is the MCP standard for bidirectional communication with streaming support, enabling:
- Real-time streaming of MCP responses
- Progress updates during long-running operations
- Server-initiated messages within a session
- Single endpoint for all communication (simpler than deprecated SSE)

## What Changes

Add Streamable HTTP transport mode using FastMCP's built-in `streamable_http_app()`:

- Extend existing HTTP transport with streaming flag
- Use FastMCP's `streamable_http_app()` for streaming support
- Single `/mcp` endpoint for bidirectional communication
- Support both stateless and stateful sessions
- Reuse existing HTTP infrastructure (uvicorn, SSL, ports)

**CLI interface:**
```bash
mcp-guide http                          # Basic HTTP (current)
mcp-guide http --streaming              # Streamable HTTP
mcp-guide https --streaming             # Streamable HTTPS with SSL
mcp-guide http://localhost:8080/mcp     # Explicit endpoint path
```

**Implementation approach:**
- No new optional dependencies (uses existing uvicorn from [http] extra)
- Extend `HttpTransport` with `streaming` parameter
- Use `mcp.streamable_http_app()` when streaming enabled
- Keep same SSL, port, host configuration
- Single endpoint handles all communication

## Impact

- Affected specs: Extend `http-transport` capability with streaming support
- Affected code:
  - `src/mcp_guide/cli.py` - Add `--streaming` flag
  - `src/mcp_guide/transports/http.py` - Add streaming mode support
  - `src/mcp_guide/transports/__init__.py` - Pass streaming flag
  - `src/mcp_guide/main.py` - Pass streaming config
- Breaking changes: None (basic HTTP remains default)
- Dependencies: Reuses existing [http] extra with uvicorn

## Design Principles

- Minimal changes to existing HTTP transport
- Leverage FastMCP's built-in streaming support
- Single endpoint simplifies deployment
- Backward compatible with basic HTTP mode
- Reuse all existing HTTP infrastructure (SSL, ports, error handling)
