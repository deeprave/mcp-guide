# Add SSE Transport

## Why

Real-time streaming updates require Server-Sent Events (SSE) transport. HTTP request/response is insufficient for streaming MCP notifications and progress updates.

## What Changes

Add SSE transport mode as an optional dependency:

- New `mcp-guide[sse]` extra for SSE support
- CLI argument parsing for SSE mode
- SSE server implementation over HTTP
- Streaming response handling for MCP protocol
- Fatal error with installation instructions if SSE mode used without extras
- Default to `localhost:8080/sse` if no URL specified

**CLI interface:**
```bash
mcp-guide stdio                      # Default, no extras needed
mcp-guide sse                        # Shorthand for http://localhost:80/sse
mcp-guide http://localhost:8080/sse  # Explicit SSE endpoint
mcp-guide https://0.0.0.0:443/sse    # HTTPS with SSE on standard port
```

**Optional dependency:**
- Base install supports stdio only
- `pip install mcp-guide[sse]` or `uvx mcp-guide[sse]` adds SSE support
- Attempting SSE mode without extras → fatal error with clear instructions

## Impact

- Affected specs: New `sse-transport` capability
- Affected code:
  - `pyproject.toml` - Add `[sse]` extra with dependencies
  - `src/mcp_guide/cli.py` - Parse SSE mode argument
  - `src/mcp_guide/server.py` - SSE transport integration
  - `src/mcp_guide/transports/` - Extend package (optional)
  - `src/mcp_guide/transports/sse.py` - SSE server implementation (optional)
  - `src/mcp_guide/transports/base.py` - Extend transport interface for streaming
- Breaking changes: None (stdio remains default)
- Dependencies: Builds on HTTP transport foundation

## Design Principles

- Minimal changes to base system
- Transport-agnostic core
- Transport-specific code isolated in optional modules
- Reuse HTTP transport components where possible
- Clean separation between request/response and streaming transports
