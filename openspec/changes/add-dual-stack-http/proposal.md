# Proposal

## Why

Guide can serve both loopback address families through `localhost`, but its
current explicit IPv6 wildcard listener does not also accept IPv4 connections.
Operators need one explicit HTTP(S) endpoint that serves both families without
changing the safe localhost default or introducing more CLI options.

## What Changes

- Enable dual-stack listening for explicit IPv6 wildcard endpoints such as
  `http://[::]:8080` and `https://[::]:8443`.
- **BREAKING**: `[::]` will accept IPv4 as well as IPv6 connections on supported
  platforms, rather than being IPv6-only. Document this exposure change.
- Preserve localhost defaults, explicit IPv4 binds, specific IPv6 binds and
  hostname-based address resolution. `0.0.0.0` remains IPv4-only.
- Report a clear startup failure if the requested dual-stack listener cannot be
  established; do not silently provide only one address family.
- Keep the same MCP application, TLS configuration, optional authentication,
  rate limiting and transport shutdown behaviour for both address families.
- Document wildcard, loopback and hostname binding, and add behavioural tests
  that connect through both IPv4 and IPv6.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `http-transport`: Explicit IPv6 wildcard endpoints support IPv4 and IPv6
  through the same transport, with deterministic startup and socket cleanup.

## Impact

- `src/mcp_guide/transports/http.py`, transport tests, installation documentation
  and Docker deployment guidance.
- No new CLI flag, global feature flag, authentication requirement, MCP API or
  persisted configuration format.
- The current Uvicorn implementation can receive an explicitly created Python
  dual-stack socket. `migrate-hypercorn-asgi` is deferred until the upstream
  FastMCP/MCP stack no longer requires Uvicorn; this change proceeds independently.
  The required listener behaviour remains independent of the selected ASGI backend.
- Existing deployments that intentionally use `[::]` for IPv6-only exposure
  must review their bind configuration before upgrading.
