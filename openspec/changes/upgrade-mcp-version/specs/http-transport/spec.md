## MODIFIED Requirements

### Requirement: Streamable HTTP Transport Mode
The system SHALL support MCP Streamable HTTP using the FastMCP 4 handler and
a single negotiated endpoint. The transport SHALL validate and process the protocol
revision and request-identification headers required by the selected SDK and protocol
revision, without relying on private FastMCP server internals.

#### Scenario: Enable streaming with flag
- **WHEN** a user runs HTTP mode with the `--streaming` flag
- **THEN** the server SHALL use the selected FastMCP 4 Streamable HTTP handler
- **AND** one `/mcp` endpoint SHALL handle bidirectional Streamable HTTP communication

#### Scenario: Streaming with HTTPS
- **WHEN** a user runs HTTPS mode with the `--streaming` flag
- **THEN** the server SHALL use Streamable HTTP with the configured TLS settings
- **AND** streaming SHALL work over TLS

#### Scenario: Streaming flag validation
- **WHEN** a user provides the `--streaming` flag with stdio mode
- **THEN** the system SHALL report that streaming is available only for HTTP or HTTPS
- **AND** it SHALL display clear usage guidance

#### Scenario: Modern HTTP request
- **WHEN** a client sends a valid negotiated Streamable HTTP request to the configured endpoint
- **THEN** the server SHALL dispatch it through the FastMCP 4 request handler
- **AND** the application SHALL receive a request context derived from that request

#### Scenario: Missing or invalid protocol headers
- **WHEN** an HTTP request omits or supplies invalid protocol headers required by the selected protocol revision
- **THEN** the server SHALL return the protocol-compliant error response
- **AND** it SHALL NOT run application handlers

#### Scenario: HTTPS transport
- **WHEN** HTTPS mode is configured with valid TLS certificate settings
- **THEN** Streamable HTTP SHALL preserve the same protocol negotiation and request-context behavior over TLS

## ADDED Requirements

### Requirement: Modern HTTP Response Metadata
The HTTP transport SHALL preserve protocol response metadata, including request state
and cache hints, instead of embedding that metadata solely in rendered text or
JSON-encoded application strings.

#### Scenario: Cacheable response
- **WHEN** an application result is explicitly marked cacheable
- **THEN** the HTTP response SHALL include the required modern cache metadata with a defined TTL and scope
- **AND** the rendered content SHALL remain unchanged by metadata transport

#### Scenario: Non-cacheable response
- **WHEN** a response contains request-specific instructions, state, or project-sensitive data without a safe cache policy
- **THEN** the system SHALL not advertise it as cacheable
