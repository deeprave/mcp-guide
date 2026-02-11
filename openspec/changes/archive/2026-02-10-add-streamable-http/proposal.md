# Add Streamable HTTP Transport

## Status: Complete

## Why

Add HTTP/HTTPS network transport to mcp-guide using MCP's Streamable HTTP protocol. This enables remote access to the MCP server over the network, supporting both local development and production deployments.

## What Changed

Implemented HTTP/HTTPS transport using FastMCP's built-in `streamable_http_app()`:

- Added HTTP/HTTPS transport modes to CLI
- Configurable path prefixes for API versioning (e.g., `/v1/mcp`, `/api/v2/mcp`)
- SSL/TLS support with flexible certificate configuration
- Combined certificate bundles (cert + key in one file)
- Automatic `/mcp` endpoint handling
- Path normalization and validation

**CLI interface:**
```bash
mcp-guide http                          # HTTP on localhost:8080
mcp-guide https --ssl-certfile cert.pem # HTTPS with SSL
mcp-guide http://localhost:8080/v1      # Custom path prefix
```

**Key features:**
- Single `/mcp` endpoint for all communication (MCP Streamable HTTP standard)
- Optional path prefixes for versioned APIs
- SSL certificate bundles supported
- Automatic path normalization (strips leading/trailing slashes)
- Smart `/mcp` handling (no duplication if path already ends with `mcp`)

## Impact

- New capability: HTTP/HTTPS network transport
- Affected code:
  - `src/mcp_guide/cli.py` - URL parsing with path support
  - `src/mcp_guide/transports/http.py` - HTTP transport implementation
  - `src/mcp_guide/transports/__init__.py` - Transport factory
  - `src/mcp_guide/main.py` - Configuration passing
  - `README.md` - Documentation and examples
- Breaking changes: None (stdio remains default)
- Dependencies: Optional `[http]` extra with uvicorn and starlette

## Design Decisions

- FastMCP uses Streamable HTTP by default - no flag needed
- Path prefix is configurable via URL (not hardcoded)
- SSL keyfile is optional when key is in certificate file
- Validation happens at server start (not CLI parse time)
- Consistent error handling with MissingDependencyError
