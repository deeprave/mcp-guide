# http-transport Specification

## Purpose
Define Guide's MCP Streamable HTTP transport and its request handling.

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

### Requirement: HTTP inbound request admission

HTTP and HTTPS SHALL admit at most the configured per-session and per-process
request rates measured in a rolling 15-second window. Defaults are
`http-session-rate-limit: 5` and `http-service-rate-limit: 100` requests per
second. Before an MCP session is established, only the process-wide limit
applies.

The limiter SHALL use FastMCP's live Streamable HTTP session registry to decide
whether a supplied session identifier is established. It SHALL not retain local
counter state for unknown identifiers and SHALL remove a session counter after
its rolling window expires.

The session limit SHALL return HTTP 429; the process-wide limit SHALL return
HTTP 503. Both SHALL include `Retry-After` for the earliest expiring admitted
request. Rejected requests SHALL not consume capacity, so retries become
available naturally as the rolling window expires. Stdio SHALL not use this
limiter.

#### Scenario: An established session reaches its request capacity
- **WHEN** an HTTP request would exceed the session's 15-second capacity
- **THEN** the server returns HTTP 429 with `Retry-After`

### Requirement: Localhost transport defaults
Bare HTTP and HTTPS modes, and transport URLs without a host, SHALL bind to
localhost. Listening on another interface, including all interfaces, SHALL
require an explicit host in the transport URL. This bind default SHALL NOT
introduce a requirement to configure authentication for remote access.

#### Scenario: HTTPS has no explicit host
- **GIVEN** HTTPS is selected without an explicit host
- **WHEN** HTTPS is selected without an explicit host
- **THEN** Guide SHALL bind to localhost

#### Scenario: All-interface endpoint is explicit
- **GIVEN** the transport URL explicitly specifies a bind address
- **WHEN** the transport URL specifies `0.0.0.0` as its host
- **THEN** Guide SHALL retain that explicitly requested bind address
- **AND** provider selection SHALL remain optional

### Requirement: Provider-backed remote ingress
When an authentication provider is selected with `--auth-provider`, a remote
MCP transport SHALL start the provider before accepting protected operations
and make its opaque request authorisation available to the application
boundary. Direct HTTPS ingress MAY pass ephemeral request authentication
evidence to the provider. A transport without a selected provider SHALL
preserve its existing protocol and access behaviour.

#### Scenario: HTTP(S) dispatches an authorised request
- **GIVEN** an authentication provider is selected for the remote transport
- **WHEN** a remote HTTP or HTTPS transport receives a protected operation
- **THEN** it SHALL pass ephemeral request authentication evidence to the
  selected provider before application dispatch
- **AND** it SHALL dispatch the operation only when the resulting request
  scopes satisfy that operation's requirement

#### Scenario: Provider is absent
- **GIVEN** no authentication provider is selected
- **WHEN** a remote transport starts without a selected provider
- **THEN** it SHALL preserve existing protocol negotiation and operation access
  behaviour

### Requirement: Deployment-owned transport security
Guide SHALL activate a selected provider for either HTTP or HTTPS and SHALL
not enforce TLS, reverse-proxy, or header-trust policy itself. Direct HTTPS or
HTTP behind TLS-terminating infrastructure are recommended deployment designs.
The deployment administrator and the configured provider SHALL determine which
request evidence is acceptable.

#### Scenario: TLS terminates at a reverse proxy
- **GIVEN** a provider is selected for a Guide HTTP upstream behind a TLS-terminating reverse proxy
- **WHEN** a provider is selected for a Guide HTTP upstream behind a
  TLS-terminating reverse proxy
- **THEN** Guide SHALL activate the provider and pass the request evidence it
  receives to that provider
- **AND** it SHALL not impose additional TLS or proxy policy
