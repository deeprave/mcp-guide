## ADDED Requirements

### Requirement: Direct HTTP/2 Streamable HTTP Serving
The system SHALL serve its FastMCP Streamable HTTP application directly through
an ASGI server capable of HTTP/2. It SHALL preserve HTTP/1.1 interoperability
when HTTP/2 is unavailable or not negotiated.

#### Scenario: HTTPS client negotiates HTTP/2
- **WHEN** HTTPS mode has valid TLS settings and the client supports HTTP/2
- **THEN** the server SHALL allow the client to use HTTP/2 for the configured MCP endpoint
- **AND** concurrent MCP requests and SSE streams SHALL remain independently processable

#### Scenario: HTTP/1.1 client connects
- **WHEN** a client connects without HTTP/2 support
- **THEN** the configured MCP endpoint SHALL remain available over HTTP/1.1
- **AND** Streamable HTTP behaviour and protocol negotiation SHALL remain unchanged

#### Scenario: HTTP/2-capable server cannot start
- **WHEN** the configured HTTP transport cannot initialise its ASGI server
- **THEN** the system SHALL report a clear startup failure
- **AND** it SHALL NOT present the MCP endpoint as available
