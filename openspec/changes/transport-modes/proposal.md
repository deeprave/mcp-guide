# Change: Multiple Transport Modes

## Why

Current implementation only supports STDIO transport, limiting usage to local CLI tools. Need support for:
- Web applications requiring HTTP/HTTPS
- Real-time updates via SSE
- Bidirectional streaming via WebSocket
- Multiple concurrent clients
- Remote access with proper authentication

## What Changes

Add support for multiple MCP transport modes:
- HTTP transport for web applications
- SSE (Server-Sent Events) for streaming updates
- WebSocket for bidirectional communication
- HTTPS + OAuth for secure remote access
- Document operation security based on transport mode
- CLI options for transport configuration

## What Changes

Add support for multiple MCP transport modes:
- HTTP transport for web applications
- SSE (Server-Sent Events) for streaming updates
- WebSocket for bidirectional communication
- Transport security model for network transports
- CLI options for transport configuration

**Implementation order:**
1. `transport-security` (defines security model)
2. `http-transport` (depends on transport-security)
3. `sse-transport` (depends on transport-security)
4. `websocket-transport` (depends on transport-security)

## Impact

- Affected specs: `http-transport`, `sse-transport`, `websocket-transport`, `transport-security` (all new capabilities)
- Affected code:
  - `src/mcp_guide/server.py` (add transport options)
  - `src/mcp_guide/cli.py` (add CLI options)
  - `src/mcp_guide/security.py` (new module for auth)
  - Configuration file support (future)
