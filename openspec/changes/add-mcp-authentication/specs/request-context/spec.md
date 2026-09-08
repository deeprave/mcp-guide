## ADDED Requirements

### Requirement: Credential-free request authorisation context
For HTTP(S) requests, the application request context SHALL expose the
transport-validated caller identity and granted scopes needed for an
authorisation decision. It SHALL not expose raw credentials, bearer tokens,
authentication headers, or transport-specific request objects. For stdio
requests, the context SHALL represent the transport as trusted for
authorisation purposes without requiring a caller identity.

#### Scenario: HTTP(S) request has an authenticated principal
- **WHEN** HTTP(S) authentication validates a caller before application
  dispatch
- **THEN** the application request context SHALL expose that caller's identity
  and scopes for the duration of the request
- **AND** it SHALL not expose the presented credential

#### Scenario: Stdio request enters the application boundary
- **WHEN** a stdio MCP request enters the application boundary
- **THEN** its request context SHALL permit protected-operation checks to
  recognise the trusted stdio transport
- **AND** it SHALL not require an identity or scope assertion
