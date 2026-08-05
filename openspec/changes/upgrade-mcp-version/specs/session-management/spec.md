## MODIFIED Requirements

### Requirement: Session Lifecycle Management
The system SHALL separate durable project configuration from request-scoped and
cross-request interaction state. Correct request handling SHALL NOT require one
mutable Session instance to exist for the lifetime of a client connection.

Project configuration and project-scoped services SHALL be resolved using an explicit
request context and owner key. If the implementation retains an in-memory session-like
object as an optimisation, it SHALL be recreatable from validated request state and
SHALL NOT be keyed solely by a FastMCP or MCP connection object.

#### Scenario: Stateless request resumes selected project
- **WHEN** a valid request presents an unexpired selected-project state
- **THEN** the system SHALL resolve the same project configuration without a prior live connection
- **AND** project-bound behavior SHALL be equivalent to a request that supplied valid roots

#### Scenario: Request has no project context
- **WHEN** a request supplies neither valid roots nor valid selected-project state
- **THEN** the system SHALL create no persisted project configuration as a side effect
- **AND** project-bound operations SHALL use the defined no-project behavior

#### Scenario: Concurrent contexts are isolated
- **WHEN** two requests carry different explicit owner or project identities
- **THEN** their transient state, listeners, and project-scoped data SHALL remain isolated
- **AND** one request SHALL NOT replace another request's active project context

## ADDED Requirements

### Requirement: Request-Scoped Client Context Refresh
The system SHALL refresh roots, client metadata, and agent metadata only from a
context-bearing MCP request or validated request state. It SHALL not request roots
from a client through a private server-session API or process a roots change through a
patched low-level message handler.

#### Scenario: Request supplies changed roots
- **WHEN** a subsequent valid request supplies roots for a different project
- **THEN** the system SHALL bind that request context to the newly resolved project
- **AND** it SHALL run the defined project-change lifecycle for that context

#### Scenario: Background work has no client request
- **WHEN** background work runs without a current request context
- **THEN** it SHALL NOT issue a server-to-client roots request
- **AND** it SHALL only operate on explicitly owned project state
