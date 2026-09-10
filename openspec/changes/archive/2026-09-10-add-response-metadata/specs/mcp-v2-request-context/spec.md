## MODIFIED Requirements

### Requirement: Framework-Neutral Request Context
The system SHALL define a framework-neutral request-context adapter for MCP tool,
prompt, and resource operations. The context SHALL expose the negotiated protocol
revision, request identity, client and agent metadata when supplied, an explicit
validated root binding and active configuration-project selection when available, and
safe response metadata APIs.

Each established Session SHALL retain an immutable protocol type derived from the
negotiated revision: `mcp_2026_07_28` for MCP `2026-07-28`, otherwise `legacy`.
The exact revision SHALL remain available for protocol-establishment logging. A request
that resolves an established Session under a different protocol type SHALL fail rather
than change that Session's response contract.

This change confines request-context construction to the FastMCP boundary.
Propagating the resolved context through application handlers is deferred to
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

#### Scenario: Modern protocol type is established
- **WHEN** a Session is first established through a request negotiated as `2026-07-28`
- **THEN** its protocol type is `mcp_2026_07_28`
- **AND** later requests using that Session retain the same type

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
- **AND** the result SHALL direct the agent to call project selection with an absolute
  client filesystem `path`, not a project name

#### Scenario: Stdio context has inherited client PWD
- **GIVEN** stdio filesystem sharing has been verified
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

#### Scenario: Retained protocol type is established
- **WHEN** a Session is first established through any retained protocol revision
- **THEN** its protocol type is `legacy`
- **AND** later requests using that Session retain the same type

#### Scenario: Protocol type mismatch
- **WHEN** a request resolves an established Session with a different protocol type
- **THEN** the request fails before response adaptation
- **AND** the existing Session protocol type remains unchanged
