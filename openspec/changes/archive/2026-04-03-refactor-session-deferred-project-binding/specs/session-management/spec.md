## MODIFIED Requirements

### Requirement: Session Non-Singleton
The system SHALL implement Session as a non-singleton class. One Session exists per
client connection. In HTTP transport, each concurrent client has its own Session via
ContextVar task isolation.

Each Session instance SHALL own its own listener list and manage listener registration
as instance methods (`add_listener`, `remove_listener`, `clear_listeners`).

Listeners SHALL NOT be shared across Session instances.

Each Session instance SHALL be allowed to exist before its real project is bound.
Before binding, the session SHALL still expose a concrete placeholder project object
rather than `None`.

The placeholder project SHALL be a wrapper around project behavior that mimics safe
real-project operations where appropriate and raises an explicit exception for
operations that require a real bound project.

#### Scenario: Session creation before project binding
- **WHEN** `get_session()` or equivalent startup logic creates a session before client project context is available
- **THEN** a Session instance is created and stored in the ContextVar
- **AND** the session contains a placeholder project object
- **AND** the session does not require a real `Project` constructor argument at creation time
- **AND** no persisted project config is loaded yet

#### Scenario: Unbound placeholder rejects bound-only operations
- **WHEN** code calls a project operation on the placeholder that requires a real persisted project
- **THEN** the placeholder SHALL raise `NoProjectError`, or allow an existing `NoProjectError` path to bubble
- **AND** it SHALL NOT silently invent or persist project data

#### Scenario: Session creation with immediate project context
- **WHEN** `get_session(ctx)` is called and project identity can be resolved immediately
- **THEN** a new Session is created
- **AND** the real project is bound during session creation
- **AND** subsequent `get_session()` calls return the same instance

### Requirement: Lazy Config Loading
The system SHALL load project config lazily via async method.

The system SHALL support deferred project binding, where a Session may begin with a
placeholder project and load the real persisted project only when a context-bearing
operation first requires it.

#### Scenario: First config access after deferred creation
- **WHEN** a session exists with a placeholder project and a project-dependent operation is invoked with sufficient context
- **THEN** the session resolves the real project identity
- **AND** loads the persisted project config
- **AND** replaces the placeholder with the real project
- **AND** subsequent accesses use the bound project

#### Scenario: Valid MCP context triggers binding
- **WHEN** a tool, prompt, or resource access provides valid MCP context
- **AND** the session is still using a placeholder project
- **AND** the cached roots are sufficient to resolve a project name
- **THEN** the session SHALL bind to the resolved real project during that access
- **AND** later accesses SHALL observe the bound project

#### Scenario: Explicit project selection binds unbound session
- **WHEN** a session exists with a placeholder project and `set_project(project_name)` is invoked
- **THEN** the session binds directly to the requested project name
- **AND** it SHALL NOT require prior auto-resolution from MCP roots or `PWD`
- **AND** the requested project config is loaded or created using the explicit project name

#### Scenario: Placeholder project is never persisted
- **WHEN** a session has not yet bound a real project
- **THEN** the placeholder project SHALL NOT be written to config storage
- **AND** no new persisted project SHALL be created from placeholder state alone

#### Scenario: Persistence boundary rejects unbound project
- **WHEN** a config-write or persistence path receives the placeholder project
- **THEN** that boundary SHALL either raise `NoProjectError` or intentionally no-op, according to the call site's defined behavior
- **AND** it SHALL NOT serialize, save, rename, or otherwise persist the placeholder as a real project

### Requirement: Session Lifecycle Management
The system SHALL maintain a single session for the lifetime of the client connection.

#### Scenario: Session persists from unbound to bound state
- **WHEN** a session is created before project context exists and later binds to a real project
- **THEN** the same Session instance is retained
- **AND** runtime listeners and state remain attached to that instance
- **AND** project-scoped data is initialized only after binding

#### Scenario: Unbound state suppresses project events
- **WHEN** the session is still using the placeholder project
- **THEN** project-related load or switch events SHALL NOT be fired
- **AND** the first real bind SHALL use the existing initial project-load notification semantics

### Requirement: Unified Session Access
The system SHALL provide a single `get_session()` async function that replaces both
`get_or_create_session` and `get_current_session`.

#### Scenario: Signature
- **WHEN** `get_session` is defined
- **THEN** its signature SHALL be `async def get_session(ctx=None, *, project_name=None, _config_dir_for_tests=None) -> Session`
- **AND** it SHALL never return None

#### Scenario: Startup access before context
- **WHEN** `get_session()` is called without `ctx` during server startup
- **THEN** it MAY return a session with a placeholder project
- **AND** it SHALL NOT require server cwd as a fallback for client project resolution
- **AND** project-bound operations SHALL require a later binding step
