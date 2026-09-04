## Purpose

Define the server lifecycle and the boundary between process startup and
client-bound MCP interactions.

## Requirements

### Requirement: Distinct Server And Client Initialization Phases
The system SHALL distinguish process-level server startup from negotiated,
request-scoped MCP dispatch.

Server startup SHALL NOT assume client roots, request context, project identity, or a
durable client connection. The server SHALL negotiate a supported MCP protocol
revision before dispatching context-bearing operations and SHALL use only supported
public SDK APIs for lifecycle and request handling.

The system SHALL construct the public FastMCP 4 surface without accepting requests
or creating client interaction state. A `GuideRuntime` SHALL perform configuration,
process initialization, and shutdown explicitly; it SHALL start before the selected
transport accepts requests and stop context-owned Guide Sessions before process
services are torn down. `GuideRuntime` SHALL retain only the Session registry,
lifecycle, service factories, coordination locks, and the shared durable
ConfigManager created at runtime startup. Configuration operations SHALL remain
Session-mediated rather than exposing ConfigManager as a general-purpose application
service. Mutable agent, active-project selection, rendering, and task
state SHALL belong to a context-owned Guide Session.

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

#### Scenario: Startup runs before client context exists
- **WHEN** the server process starts before any client request arrives
- **THEN** it SHALL perform only process-level and project-independent initialization
- **AND** it SHALL NOT create a client-bound session or infer project identity from server process state

#### Scenario: Server construction has no startup side effects
- **WHEN** server construction registers the MCP surface
- **THEN** it SHALL NOT accept a transport connection, create a context-owned Guide Session, or start task timers
- **AND** `GuideRuntime.start()` SHALL perform the current process initialization exactly once before request acceptance

#### Scenario: Controlled shutdown
- **WHEN** the selected transport stops or startup fails after the runtime begins
- **THEN** the system SHALL stop affected Guide Sessions, their task managers, watchers, and timers before stopping process-level services
- **AND** repeated shutdown calls SHALL be safe

#### Scenario: Modern protocol request is negotiated
- **WHEN** a client negotiates a supported MCP protocol revision
- **THEN** the server SHALL dispatch requests through the modern request-scoped entry point
- **AND** it SHALL expose the negotiated revision to the application request context

#### Scenario: Unsupported protocol revision
- **WHEN** a client requests an unsupported MCP protocol revision
- **THEN** the server SHALL reject the request using the selected SDK's protocol-compliant response
- **AND** it SHALL NOT execute project-bound application logic

#### Scenario: Agent selects a project
- **WHEN** an agent determines its project root and invokes Guide's explicit project-selection operation
- **THEN** the operation SHALL require an absolute client filesystem argument named `path`
- **AND** the server SHALL derive root identity from that path, bind the interaction to the selected root, and preserve that selection in validated interaction state
- **AND** it SHALL NOT rely on roots, a mutable connection-bound session, or server cwd

#### Scenario: Inherited PWD bootstrap is off by default
- **WHEN** a sessionless stdio interaction arrives with a valid absolute inherited `PWD`
- **AND** inherited-PWD bootstrap has not been explicitly enabled
- **THEN** the server SHALL NOT bind a project from `PWD`
- **AND** the agent SHALL use `set_project(path)` to bind the client root

#### Scenario: Stdio CLI process opts into inherited PWD binding
- **WHEN** inherited-PWD bootstrap is explicitly enabled
- **AND** a sessionless stdio interaction is handled by a Guide process started with a
  valid absolute inherited `PWD`
- **THEN** the request adapter SHALL treat that path as the CLI client's launch
  project path and bind the newly created interaction to it immediately
- **AND** it SHALL add that Session to `GuideRuntime` without requiring a
  `set_project(path)` round trip
- **AND** it SHALL apply the same immutable-root and strict configuration-hash rules
  as explicit project selection
- **AND** it SHALL not infer a root from `PWD` when the request supplies a `session_id`
- **AND** it SHALL NOT treat server `getcwd()` as the client filesystem root

#### Scenario: Remote process has no project path
- **WHEN** an unbound HTTP or other remote interaction is handled
- **THEN** the server SHALL NOT use its process `PWD` or working directory to infer
  the client's project
- **AND** the agent SHALL use `set_project(path)` to bind it

#### Scenario: Agent repeats project-root binding
- **WHEN** an interaction already bound to one root invokes `set_project`, with any `path`
- **THEN** the server SHALL reject the request and direct the agent to begin a new interaction for a different root
- **AND** it SHALL NOT mutate the existing interaction's root, task state, or queued instructions

#### Scenario: Agent changes active configuration project
- **WHEN** a root-bound interaction invokes `switch_project` with a configuration name
- **THEN** the server SHALL change the active Guide configuration project using that name
- **AND** it SHALL NOT treat the name as a filesystem path or alter the interaction's bound root
