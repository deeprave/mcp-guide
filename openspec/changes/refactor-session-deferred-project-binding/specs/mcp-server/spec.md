## ADDED Requirements

### Requirement: Distinct Server And Client Initialization Phases
The system SHALL distinguish between process-level server startup and client/project-bound initialization.

Server startup SHALL NOT assume that client roots, request context, or project identity
are already available.

#### Scenario: Startup runs before client roots exist
- **WHEN** `@mcp.on_init()` handlers run during server startup
- **THEN** they SHALL perform only process-level or project-independent initialization
- **AND** any client/project-sensitive work SHALL be deferred until a later context-bearing operation

#### Scenario: Real project binding happens from client context
- **WHEN** a later tool, prompt, resource, or equivalent context-bearing operation arrives
- **THEN** the server MAY complete deferred project-bound initialization from that client context
- **AND** it SHALL NOT infer client project identity from server process cwd

#### Scenario: Any valid context-bearing access may perform first bind
- **WHEN** any tool, prompt, or resource access arrives with valid MCP context
- **AND** the active session is still unbound
- **THEN** that access MAY trigger the first real project bind
- **AND** no separate `PWD` fallback is required for that bind path
