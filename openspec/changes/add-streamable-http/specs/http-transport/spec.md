## ADDED Requirements

### Requirement: Streamable HTTP Transport Mode
The system SHALL support Streamable HTTP transport mode for bidirectional streaming communication.

#### Scenario: Enable streaming with flag
- **WHEN** user runs with `--streaming` flag on HTTP mode
- **THEN** server uses FastMCP's streamable_http_app()
- **AND** single `/mcp` endpoint handles all communication
- **AND** supports bidirectional streaming

#### Scenario: Streaming with HTTPS
- **WHEN** user runs with `--streaming` flag on HTTPS mode
- **THEN** server uses streamable HTTP with SSL configuration
- **AND** SSL certificates are properly configured
- **AND** streaming works over TLS

#### Scenario: Streaming flag validation
- **WHEN** user provides `--streaming` flag with stdio mode
- **THEN** error message indicates streaming only works with HTTP/HTTPS
- **AND** clear usage instructions are displayed

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
