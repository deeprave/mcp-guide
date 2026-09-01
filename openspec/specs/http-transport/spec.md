# http-transport Specification

## Purpose
TBD - created by archiving change add-streamable-http. Update Purpose after archive.

## Requirements

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

### Requirement: Single Endpoint Communication
The system SHALL use a single endpoint for all Streamable HTTP communication.

#### Scenario: Default endpoint path
- **WHEN** streaming mode is enabled without explicit path
- **THEN** server listens on `/mcp` endpoint
- **AND** all client requests go to this single endpoint

#### Scenario: Custom endpoint path
- **WHEN** user specifies URL with path like `http://localhost:8080/custom`
- **THEN** server uses `/custom` as the endpoint path
- **AND** streaming communication works on custom path

### Requirement: Backward Compatibility
The system SHALL maintain existing HTTP behavior when streaming is not enabled.

#### Scenario: Basic HTTP without streaming
- **WHEN** user runs HTTP mode without `--streaming` flag
- **THEN** server uses basic HTTP request/response pattern
- **AND** existing HTTP behavior is unchanged
- **AND** no streaming features are active

#### Scenario: Streaming disabled by default
- **WHEN** user runs `mcp-guide http`
- **THEN** streaming mode is disabled
- **AND** basic HTTP transport is used

### Requirement: Modern HTTP Response Metadata
The HTTP transport SHALL preserve supported protocol response metadata instead of
embedding that metadata solely in rendered text or JSON-encoded application strings.
It SHALL NOT emit cache TTL or scope using non-standard
`io.modelcontextprotocol/cache-*` `_meta` keys. A newly minted FastMCP `session_id`
SHALL be returned through the common structured result fixture rather than response
metadata.

#### Scenario: Response without cache metadata
- **WHEN** an application response is adapted for HTTP delivery
- **THEN** it does not include non-standard cache TTL or scope `_meta` keys
- **AND** the rendered content remains unchanged by metadata transport
