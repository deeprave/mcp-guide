## MODIFIED Requirements

### Requirement: Distinct Server And Client Initialization Phases
The system SHALL distinguish process-level server startup from negotiated,
request-scoped MCP dispatch.

Server startup SHALL NOT assume client roots, request context, project identity, or a
durable client connection. The server SHALL negotiate a supported MCP protocol
revision before dispatching context-bearing operations and SHALL use only supported
public SDK APIs for lifecycle and request handling.

#### Scenario: Startup runs before client context exists
- **WHEN** the server process starts before any client request arrives
- **THEN** it SHALL perform only process-level and project-independent initialization
- **AND** it SHALL NOT create a client-bound session or infer project identity from server process state

#### Scenario: Modern protocol request is negotiated
- **WHEN** a client negotiates a supported MCP protocol revision
- **THEN** the server SHALL dispatch requests through the modern request-scoped entry point
- **AND** it SHALL expose the negotiated revision to the application request context

#### Scenario: Unsupported protocol revision
- **WHEN** a client requests an unsupported MCP protocol revision
- **THEN** the server SHALL reject the request using the selected SDK's protocol-compliant response
- **AND** it SHALL NOT execute project-bound application logic

#### Scenario: Project binding occurs from request context
- **WHEN** a tool, prompt, or resource request supplies valid roots or selected-project state
- **THEN** the server SHALL resolve project identity from that request context
- **AND** it SHALL NOT rely on a mutable connection-bound session or server cwd
