# mcp-v2-request-context Specification

## Purpose
TBD - created by archiving change upgrade-mcp-version. Update Purpose after archive.

## Requirements

### Requirement: Framework-Neutral Request Context
The system SHALL define a framework-neutral request-context adapter for MCP tool,
prompt, and resource operations. The context SHALL expose the negotiated protocol
revision, request identity, client and agent metadata when supplied, an explicit
validated root binding and active configuration-project selection when available, and
safe response metadata APIs.

This change confines request-context construction to the FastMCP boundary. Propagating
the resolved context through application handlers is deferred to
`use-request-context`; transitional handlers may continue to receive raw FastMCP
context while using the validated Session boundary defined here.

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
- **THEN** the request adapter derives an application request context from that request
- **AND** the validated Session boundary resolves the Guide Session from the verified
  Session key without inspecting SDK-private objects
- **AND** the handler-propagation refactor remains the responsibility of
  `use-request-context`

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
- **WHEN** a sessionless stdio context has a valid absolute inherited `PWD`
- **AND** inherited-PWD bootstrap has been explicitly enabled
- **THEN** the request adapter SHALL bind the new Guide Session from that path before
  evaluating the no-project result
- **AND** it SHALL use the same runtime-owned Session and binding path as an explicit
  `set_project(path)` request
- **AND** it SHALL NOT use that shortcut by default
- **AND** it SHALL NOT use that shortcut for a remote transport
- **AND** it SHALL NOT use that shortcut when the request supplies a `session_id`
- **AND** it SHALL NOT treat server `getcwd()` as the client filesystem root

### Requirement: FastMCP Session-ID Cross-Request Binding
The system SHALL use FastMCP's minted, principal-validated `session_id` as the
explicit cross-request binding mechanism for a modern MCP interaction. The session
ID SHALL select a context-owned, in-memory Guide Session for the lifetime of the
running MCP server.

Guide SHALL persist only project configuration in its configuration file. It SHALL
NOT persist or restore root bindings, active configuration selection, instructions,
task state, or rendering caches across an MCP server restart.

#### Scenario: Valid session-ID round trip
- **WHEN** an interaction binds a root with `set_project(path)` and FastMCP mints a
  session ID
- **THEN** the common Result adapter SHALL return that `session_id` in the standard
  structured result fixture
- **AND** a subsequent request supplying that valid ID SHALL resolve the same
  in-memory Guide Session while the MCP server remains running

#### Scenario: Unknown or invalid session ID
- **WHEN** a request supplies a session ID that FastMCP does not validate for the
  current principal
- **THEN** the system SHALL reject the ID
- **AND** it SHALL not create a replacement Guide Session or use it to select a
  project or deliver queued instructions
- **AND** it SHALL return a distinct invalid-session result directing the client to
  discard that identifier and call `set_project(path)` to begin a new interaction

#### Scenario: MCP server restart
- **WHEN** the MCP server is restarted
- **THEN** its prior Guide Sessions and transient state SHALL be discarded
- **AND** a new interaction SHALL bind a project before project-bound behaviour is
  available
- **AND** persisted project configuration MAY be loaded after that binding

### Requirement: Explicit Interaction Ownership
The system SHALL partition cross-request queued instructions, project-scoped tasks,
and transient rendering state by an explicit interaction owner and project identity.
Ambient `ContextVar` state and SDK connection objects SHALL NOT be the source of
cross-request ownership.

#### Scenario: Concurrent project requests
- **WHEN** requests for different clients or projects are processed concurrently
- **THEN** instructions and transient state created for one request SHALL NOT be delivered to the other
- **AND** project-scoped work SHALL use the owner and project identity of its originating context
