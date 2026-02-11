# Add HTTP/HTTPS Transport

## Why

Current implementation only supports stdio transport, limiting usage to local CLI tools. Web applications and remote access require HTTP/HTTPS transport support.

## What Changes

Add HTTP/HTTPS transport mode as an optional dependency:

- New `mcp-guide[http]` extra for HTTP/HTTPS support (uvicorn)
- CLI argument parsing for `http://` and `https://` URLs
- HTTP server using MCP's built-in streamable HTTP support
- Request/response handling for MCP protocol over HTTP via FastMCP
- Fatal error with installation instructions if HTTP mode used without extras
- Default to `localhost:8080` for HTTP, `0.0.0.0:443` for HTTPS

**CLI interface:**
```bash
mcp-guide stdio                      # Default, no extras needed
mcp-guide http                       # Shorthand for http://localhost:8080
mcp-guide http://:3000               # Explicit localhost:3000
mcp-guide http://localhost:8080      # Explicit host:port
mcp-guide https                      # Shorthand for https://0.0.0.0:443
mcp-guide https://:8443              # Explicit 0.0.0.0:8443
mcp-guide https://0.0.0.0:8443       # Explicit binding to all interfaces
```

**Binding defaults:**
- `http` → `localhost:8080` (local only, non-privileged port)
- `https` → `0.0.0.0:443` (all interfaces, standard HTTPS port)
- Empty host (`:port`) → `localhost` for HTTP, `0.0.0.0` for HTTPS

**Optional dependency:**
- Base install supports stdio only
- `uv sync --extra http` or `uvx --with uvicorn mcp-guide` adds HTTP support
- Attempting HTTP mode without extras → fatal error with clear instructions

**Implementation:**
- Uses FastMCP's `streamable_http_app()` for MCP protocol handling
- Uvicorn serves the Starlette ASGI app
- All MCP tools, resources, and prompts work over HTTP

## Impact

- Affected specs: New `http-transport` capability
- Affected code:
  - `pyproject.toml` - Add `[http]` extra with uvicorn dependency
  - `src/mcp_guide/cli.py` - Parse transport mode argument
  - `src/mcp_guide/server.py` - Transport abstraction
  - `src/mcp_guide/transports/` - New package
  - `src/mcp_guide/transports/http.py` - HTTP server using FastMCP + uvicorn
  - `src/mcp_guide/transports/base.py` - Transport interface
- Breaking changes: None (stdio remains default)

## Design Principles

- Minimal changes to base system
- Transport-agnostic core
- Transport-specific code isolated in optional modules
- No transport-specific features in core logic
- Clean separation between stdio and network transports
