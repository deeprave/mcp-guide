## Context

See [proposal.md](proposal.md) for motivation. The current transport constructs
FastMCP's ASGI application and starts it with Uvicorn. Uvicorn does not provide
direct HTTP/2 serving, while Hypercorn supports HTTP/1.1, HTTP/2, and ASGI.

## Goals / Non-Goals

**Goals:**

- Replace the built-in ASGI server with Hypercorn for direct HTTP/2-capable
  Streamable HTTP serving.
- Retain the existing CLI transport configuration, TLS options, endpoint-path
  rules, FastMCP ASGI application ownership, and graceful shutdown behaviour.
- Test HTTP/1.1 compatibility and verify HTTP/2-capable configuration without
  requiring external network infrastructure in ordinary tests.

**Non-Goals:**

- Add WebSocket transport, HTTP/3 deployment support, reverse-proxy management,
  or changes to MCP request/session-handle semantics.
- Expose the HTTP protocol version to Guide application handlers.

## Decisions

### Use Hypercorn as the built-in ASGI server

Hypercorn replaces Uvicorn in the optional HTTP dependency group and in
`HttpTransport`. It accepts the existing FastMCP ASGI application directly and
supports TLS ALPN negotiation for HTTP/2 while preserving HTTP/1.1 fallback.

The alternative of keeping Uvicorn and documenting an external HTTP/2 proxy
does not provide direct HTTP/2 serving. A configurable server abstraction is
unnecessary: mcp-guide has one built-in HTTP transport and this change selects
its required server.

### Preserve FastMCP at the MCP boundary

`HttpTransport` continues to obtain the ASGI application from FastMCP. Hypercorn
only serves that application; it does not parse, route, or adapt MCP messages.
This keeps protocol negotiation, endpoint handling, and request context creation
unchanged.

### Run Hypercorn through its asynchronous API

The transport will use Hypercorn's asynchronous serving API with an explicit
shutdown trigger. This preserves mcp-guide's non-blocking `start()` and awaited
`stop()` lifecycle instead of spawning a separate process or replacing the
application event loop.

## Risks / Trade-offs

- [Hypercorn configuration differs from Uvicorn] → Map existing host, port,
  certificate, key, logging, and shutdown behaviour in focused transport tests.
- [HTTP/2 is only negotiated with suitable TLS/client support] → Preserve and
  document HTTP/1.1 fallback; do not claim HTTP/2 for plain HTTP deployments.
- [Optional dependency migration breaks existing installations] → Keep HTTP
  dependencies optional and provide a clear missing-dependency error.

## Migration Plan

1. Replace the optional dependency and update lock data.
2. Refactor `HttpTransport` to configure and serve FastMCP's ASGI application
   through Hypercorn.
3. Update transport tests and user installation/deployment documentation.
4. Run focused HTTP tests and the full strict verification suite.

Rollback is a source and dependency rollback to the prior Uvicorn transport;
there is no persisted-data or protocol-format migration.
