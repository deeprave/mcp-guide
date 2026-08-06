## ADDED Requirements

### Requirement: Framework-Neutral Request Context
The system SHALL construct a framework-neutral request context for every MCP tool,
prompt, and resource operation. The context SHALL expose the negotiated protocol
revision, request identity, client and agent metadata when supplied, roots when
supplied, an explicit project selection when valid, and safe response metadata APIs.

Application services SHALL NOT require a raw FastMCP context or a low-level MCP
server-session object to perform correct request handling.

#### Scenario: Context-bearing tool request
- **WHEN** a negotiated MCP tool request is dispatched
- **THEN** its handler receives an application request context derived from that request
- **AND** the handler can resolve the request's client metadata and roots without inspecting SDK-private objects

#### Scenario: Context is unavailable
- **WHEN** an MCP request does not supply roots or prior selected project state
- **THEN** the request context SHALL represent project identity as unavailable
- **AND** project-bound operations SHALL return the defined no-project result
- **AND** the server SHALL NOT infer client identity from its process working directory

### Requirement: Integrity-Protected Cross-Request State
The system SHALL use an integrity-protected, expiry-bound request-state representation
for state that must survive a modern MCP multi-round-trip interaction. State SHALL be
bound to the available client or principal scope and to the request authorisation
context it represents.

#### Scenario: Valid selected-project state round trip
- **WHEN** an interaction selects a project and the protocol requires state to round trip
- **THEN** the response SHALL return the selected project through the supported request-state mechanism
- **AND** a subsequent valid request SHALL recover that selection without a live connection object

#### Scenario: Tampered or expired state
- **WHEN** a request presents request state with an invalid signature, incompatible binding, or expired timestamp
- **THEN** the system SHALL reject that state
- **AND** it SHALL NOT use the state to select a project or deliver queued instructions

### Requirement: Explicit Interaction Ownership
The system SHALL partition cross-request queued instructions, project-scoped tasks,
and transient rendering state by an explicit interaction owner and project identity.
Ambient `ContextVar` state and SDK connection objects SHALL NOT be the source of
cross-request ownership.

#### Scenario: Concurrent project requests
- **WHEN** requests for different clients or projects are processed concurrently
- **THEN** instructions and transient state created for one request SHALL NOT be delivered to the other
- **AND** project-scoped work SHALL use the owner and project identity of its originating context
