## MODIFIED Requirements

### Requirement: Session Non-Singleton
The system SHALL implement Session as a non-singleton class. One Session exists per
client connection. In HTTP transport, each concurrent client has its own Session via
ContextVar task isolation.

Each Session instance SHALL own its own listener list and manage listener registration
as instance methods (`add_listener`, `remove_listener`, `clear_listeners`).

Listeners SHALL NOT be shared across Session instances.

#### Scenario: Session creation
- **WHEN** `get_session()` is called and no session exists in the current async context
- **THEN** a new Session is created with auto-resolved project name
- **AND** the session is stored in the ContextVar
- **AND** subsequent `get_session()` calls return the same instance

#### Scenario: Name format validation
- **WHEN** Session is created with empty or whitespace-only project name
- **THEN** ValueError is raised immediately
- **AND** session is not created

#### Scenario: Concurrent HTTP clients isolated
- **WHEN** multiple clients connect via HTTP transport
- **THEN** each client has its own Session instance via ContextVar task isolation
- **AND** session state for one client does not affect another
- **AND** each session has its own listener list and cache state

#### Scenario: Listener isolation
- **WHEN** Session A registers a listener
- **THEN** that listener is only notified of changes on Session A
- **AND** Session B's listeners are unaffected

### Requirement: Session Lifecycle Management
The system SHALL maintain a single session for the lifetime of the client connection.

#### Scenario: Session persists across project switches
- **WHEN** the active project is switched via `set_project`
- **THEN** the same Session instance is retained
- **AND** project-scoped data is reloaded on the existing session

#### Scenario: Session cleanup
- **WHEN** the MCP server shuts down or the client disconnects
- **THEN** session resources are released

## ADDED Requirements

### Requirement: Session Listener Protocol
The system SHALL define a `SessionListener` protocol with two notification methods:

- `on_project_changed(session, old_project, new_project)` — called when a project is loaded or switched
- `on_config_changed(session)` — called when project configuration is modified

Listeners SHALL be registered per-session via `session.add_listener(listener)`.

#### Scenario: Initial project load notification
- **WHEN** a session is created with its initial project
- **THEN** `on_project_changed(session, "", project_name)` is called on all session listeners

#### Scenario: Project switch notification
- **WHEN** `switch_project()` is called and the project name differs from the current one
- **THEN** `on_project_changed(session, old_name, new_name)` is called on all session listeners

#### Scenario: Same project switch is no-op
- **WHEN** `switch_project()` is called with the same project name
- **THEN** no listener notifications are fired

### Requirement: Per-Session Template Context Cache
The system SHALL maintain template context cache state per-session, not as a module-level global.

`TemplateContextCache` SHALL be instantiated per session and registered as a session listener.
Cache invalidation on one session SHALL NOT affect other sessions.

#### Scenario: Cache isolation between sessions
- **WHEN** Session A switches project and invalidates its template cache
- **THEN** Session B's template cache is unaffected

#### Scenario: Cache invalidation on project change
- **WHEN** `on_project_changed` is called on the template cache listener
- **THEN** the cache is invalidated for that session only

#### Scenario: Cache invalidation on config change
- **WHEN** `on_config_changed` is called on the template cache listener
- **THEN** the cache is invalidated for that session only
