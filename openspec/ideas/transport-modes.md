# Idea: Multiple Transport Modes

**Status:** Future Enhancement
**Priority:** Post-MVP
**Created:** 2025-11-25

## Overview

Support multiple MCP transport modes beyond the initial STDIO implementation.

## Transport Modes

### 1. STDIO (Initial Implementation)
- **Status**: Implemented in MVP
- **Use Case**: CLI tools, desktop applications (Claude Desktop, Kiro CLI)
- **Pros**: Simple, no network configuration needed
- **Cons**: Local only, single client

### 2. HTTP (Next Priority)
- **Status**: Planned
- **Use Case**: Web applications, remote access, multiple clients
- **Pros**: Standard protocol, firewall-friendly, stateless
- **Cons**: Request/response only, no streaming
- **Implementation**: FastMCP supports via `mcp.run(transport="http", host="0.0.0.0", port=8000)`

### 3. SSE (Server-Sent Events)
- **Status**: Future
- **Use Case**: Real-time updates, streaming responses
- **Pros**: HTTP-based, server-to-client streaming
- **Cons**: One-way streaming only
- **Implementation**: FastMCP supports via `mcp.run(transport="sse", host="0.0.0.0", port=8000)`

### 4. WebSocket
- **Status**: Future
- **Use Case**: Bidirectional streaming, real-time collaboration
- **Pros**: Full-duplex communication
- **Cons**: More complex, requires WebSocket support
- **Implementation**: May require additional FastMCP configuration

## Security Considerations

### HTTPS with OAuth
- **Requirement**: For HTTP/SSE/WebSocket modes in production
- **OAuth Flow**: Standard OAuth 2.0 for authentication
- **Document Handling**: Disable document operations unless on authenticated HTTPS

### Document Security
```python
def is_document_access_allowed() -> bool:
    """Check if document operations are allowed based on transport security"""
    if transport == TransportMode.STDIO:
        return True  # Local access, trusted
    elif transport in [TransportMode.HTTP, TransportMode.SSE, TransportMode.WEBSOCKET]:
        return is_https_with_auth()  # Require HTTPS + auth
    return False
```

## CLI Interface (Future)

```python
@click.command()
@click.option("--transport", type=click.Choice(["stdio", "http", "sse", "websocket"]),
              default="stdio", help="Transport mode")
@click.option("--host", default="0.0.0.0", help="Host for network modes")
@click.option("--port", default=8000, type=int, help="Port for network modes")
@click.option("--https", is_flag=True, help="Enable HTTPS (requires cert/key)")
@click.option("--cert", type=click.Path(), help="SSL certificate file")
@click.option("--key", type=click.Path(), help="SSL key file")
@click.option("--oauth-provider", help="OAuth provider (google, github, etc.)")
@click.option("--log-level", default="INFO", help="Logging level")
def main(transport, host, port, https, cert, key, oauth_provider, log_level):
    """MCP Guide Server - Main entry point"""
    # Validate HTTPS requirements
    if https and not (cert and key):
        raise click.UsageError("HTTPS requires --cert and --key")

    # Validate OAuth requirements
    if oauth_provider and not https:
        raise click.UsageError("OAuth requires HTTPS")

    asyncio.run(async_main(...))
```

## Implementation Phases

### Phase 1: STDIO (MVP)
- Basic server with STDIO transport
- No CLI options needed
- Local access only

### Phase 2: HTTP Support
- Add HTTP transport option
- Add host/port CLI options
- Document security warnings (HTTP is unencrypted)

### Phase 3: HTTPS + OAuth
- Add SSL certificate support
- Implement OAuth flow
- Enable document operations on authenticated HTTPS

### Phase 4: SSE/WebSocket
- Add streaming transport options
- Implement real-time features
- Support multiple concurrent clients

## Configuration

Future configuration file support:

```yaml
server:
  transport: http
  host: 0.0.0.0
  port: 8000

security:
  https:
    enabled: true
    cert: /path/to/cert.pem
    key: /path/to/key.pem
  oauth:
    provider: google
    client_id: xxx
    client_secret: xxx

features:
  documents:
    enabled: true  # Only if HTTPS + auth
```

## Testing Considerations

- STDIO: Test with MCP inspector, Claude Desktop
- HTTP: Test with curl, Postman, web clients
- SSE: Test streaming with EventSource clients
- WebSocket: Test with WebSocket clients

## Related ADRs

- ADR-002: MCP Server Framework (FastMCP supports all transports)
- Future: ADR for HTTPS/OAuth implementation
- Future: ADR for document security model
