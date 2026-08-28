## ADDED Requirements

### Requirement: Framework-Neutral Request Context
The system SHALL construct a framework-neutral request context for every MCP tool,
prompt, and resource operation. The context SHALL expose the negotiated protocol
revision, request identity, client and agent metadata when supplied, an explicit
validated root binding and active configuration-project selection when available, and
safe response metadata APIs.

Application services SHALL NOT require a raw FastMCP context or a low-level MCP
server-session object to perform correct request handling.

The request adapter SHALL receive the public FastMCP context and, when the tool
arguments provide it, the FastMCP `session_id`. It SHALL use a validated explicit
`session_id` as the GuideRuntime Session key. For a retained handshake-era request
that omits that argument, it SHALL use the public FastMCP `ctx.session_id` as the
legacy connection Session key. Client name/version metadata SHALL NOT be used as a
Session key. FastMCP and raw SDK connection objects SHALL NOT own Guide Session state.

The application request context SHALL retain the resolved Session key and whether it
was explicit or legacy-derived, without exposing raw SDK connection objects to
application services.

Before either source becomes a GuideRuntime key, the adapter SHALL validate the
session ID as unstructured input. It SHALL reject empty or overlong values and C0/C1
control characters, without imposing a UUID format or other needless structure.

#### Scenario: Context-bearing tool request
- **WHEN** a negotiated MCP tool request is dispatched
- **THEN** its handler receives an application request context derived from that request
- **AND** the handler can resolve the request's client metadata, bound root, and active configuration project without inspecting SDK-private objects
- **AND** the context SHALL contain the Guide Session resolved by `GuideRuntime` from the verified Session key

#### Scenario: Tool supplies an explicit FastMCP session ID
- **WHEN** a tool argument contains a valid FastMCP `session_id`
- **THEN** the request adapter SHALL validate it through FastMCP's public session API
- **AND** it SHALL use that exact ID as the GuideRuntime Session key regardless of
  negotiated protocol era

#### Scenario: Legacy tool omits explicit session ID
- **WHEN** a handshake-era request supplies no `session_id` argument
- **THEN** the request adapter SHALL use public `ctx.session_id` to resolve the
  connection-owned Guide Session
- **AND** it SHALL preserve the current legacy connection behavior without requiring
  the client to replay a returned identifier

#### Scenario: Modern tool omits explicit session ID
- **WHEN** a modern request supplies no `session_id` outside a defined session-creation
  or stdio-PWD bootstrap operation
- **THEN** the adapter SHALL not create an unrelated replacement Session
- **AND** the project-bound operation SHALL return the defined unbound guidance

#### Scenario: Session ID contains unsafe characters
- **WHEN** an explicit argument or a FastMCP-derived legacy ID is empty, overlong, or
  contains a control character
- **THEN** the request adapter SHALL reject it before Session resolution
- **AND** it SHALL not create a GuideRuntime registry entry or include the raw value
  in user-visible diagnostics

#### Scenario: Context is unavailable
- **WHEN** an MCP request has no valid selected-root state and has not invoked `set_project(path)`
- **THEN** the request context SHALL represent root and project context as unavailable
- **AND** project-bound operations SHALL return the defined no-project result
- **AND** the server SHALL NOT infer client identity from its process working directory
  for HTTP or other remote transports
- **AND** the result SHALL direct the agent to call project selection with an absolute client filesystem `path`, not a project name

#### Scenario: Stdio context has inherited client PWD
- **WHEN** an unbound stdio context has a valid absolute inherited `PWD`
- **THEN** the request adapter SHALL bind the new Guide Session from that path before
  evaluating the no-project result
- **AND** it SHALL NOT use that shortcut for a remote transport

### Requirement: Integrity-Protected Cross-Request State
The system SHALL use the selected SDK's integrity-protected request-state facility,
configured with stable deployment keys, for state that must survive a modern MCP
multi-round-trip interaction. Application state SHALL be expiry-bound, versioned,
and bound to the available client or principal scope and to the request authorisation
context it represents.

#### Scenario: Valid selected-root state round trip
- **WHEN** an interaction binds a root with `set_project(path)` and the protocol requires state to round trip
- **THEN** the response SHALL return the bound root and active configuration selection through the supported request-state mechanism
- **AND** a subsequent valid request SHALL recover that context without a live connection object

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
