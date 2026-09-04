## Why

MCP Streamable HTTP benefits from HTTP/2 connection reuse and multiplexing when
remote clients issue concurrent requests or hold SSE streams. mcp-guide currently
starts its ASGI application with Uvicorn, which serves HTTP/1.1 only.

## What Changes

- Replace Uvicorn with Hypercorn as mcp-guide's built-in ASGI server for HTTP and
  HTTPS Streamable HTTP transport.
- Support direct HTTP/2 serving where TLS and client negotiation permit it, while
  retaining HTTP/1.1 interoperability.
- Update the optional HTTP dependency set, startup/shutdown integration, user
  documentation, and transport tests for Hypercorn.
- Preserve FastMCP's ownership of the MCP ASGI application, endpoint routing,
  protocol negotiation, and request handling.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `http-transport`: Direct HTTP transport supports HTTP/2 through Hypercorn while preserving Streamable HTTP behaviour and HTTP/1.1 compatibility.

## Impact

- Affected code: `src/mcp_guide/transports/http.py`, optional dependencies,
  CLI-facing HTTP documentation, and transport tests.
- Dependency change: replace the optional `uvicorn` dependency with Hypercorn.
- Deployment change: direct TLS deployments may negotiate HTTP/2; no MCP API,
  URI, session-handle, or project-configuration format changes are intended.
