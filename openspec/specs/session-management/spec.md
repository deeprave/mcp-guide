# session-management Specification

## Purpose
Provides session management with non-singleton sessions, lazy config loading, functional updates, and efficient MCP context caching with deduplication.
## Requirements
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

### Requirement: Lazy Config Loading
The system SHALL load project config lazily via async method.

#### Scenario: First config access
- WHEN `await session.get_project()` is called for the first time
- THEN config is loaded from ConfigManager
- AND config is cached in session
- AND subsequent calls use cached value

#### Scenario: Config not found
- WHEN project doesn't exist in config
- THEN ConfigManager creates it automatically
- AND new project is returned with default settings

### Requirement: Functional Config Updates
The system SHALL support functional config updates with automatic save.

#### Scenario: Update config
- WHEN `await session.update_config(updater)` is called
- THEN updater function receives current Project
- AND updater returns new Project
- AND new Project is saved to config file
- AND cached config is updated

#### Scenario: Update failure
- WHEN updater raises exception
- THEN config is not saved
- AND cache is not updated
- AND exception propagates to caller

### Requirement: Mutable State Access
The system SHALL provide access to mutable runtime state.

#### Scenario: State access
- WHEN `session.get_state()` is called
- THEN SessionState instance is returned
- AND state can be mutated
- AND state is not persisted to config file

### Requirement: ContextVar Session Tracking
The system SHALL track the active session per async task using a single-valued ContextVar.

#### Scenario: Single session per context
- **WHEN** `get_session()` is called
- **THEN** the ContextVar holds a single `Optional[Session]` (not a dict)
- **AND** the same session is returned for all operations in that async context

#### Scenario: Session creation on first access
- **WHEN** `get_session(ctx)` is called and no session exists
- **THEN** a session is created, project is auto-resolved, and MCP context is cached from `ctx`
- **AND** the session is stored in the ContextVar

#### Scenario: Existing session returned
- **WHEN** `get_session()` is called and a session already exists
- **THEN** the existing session is returned
- **AND** creation arguments (`ctx`, `project_name`, `_config_dir_for_tests`) are ignored

### Requirement: Session Lifecycle Management
The system SHALL maintain a single session for the lifetime of the client connection.

#### Scenario: Session persists across project switches
- **WHEN** the active project is switched via `set_project`
- **THEN** the same Session instance is retained
- **AND** project-scoped data is reloaded on the existing session

#### Scenario: Session cleanup
- **WHEN** the MCP server shuts down or the client disconnects
- **THEN** session resources are released

### Requirement: MCP Context Deduplication
The system SHALL store MCP session context (agent info, roots, client params) on the
Session object rather than in a separate module-level global.

#### Scenario: Session carries MCP context
- **WHEN** MCP context is cached via `cache_mcp_globals()`
- **THEN** agent_info, roots, and client_params are stored on the current Session instance
- **AND** no separate `CachedMcpContext` module global is used

#### Scenario: Project switch preserves session context
- **WHEN** the active project is switched
- **THEN** session identity fields (agent_info, roots, client_params) are preserved
- **AND** only project-scoped fields (project_name, categories, collections, flags) are updated

#### Scenario: Consolidated extraction
- **WHEN** session is created via `get_session(ctx)`
- **THEN** `cache_mcp_globals()` extracts all MCP context once and stores it on the session
- **AND** no redundant extraction occurs during tool execution

### Requirement: Tool Integration Pattern
The system SHALL provide helper functions for tools to access sessions.

#### Scenario: Tool accesses session
- WHEN tool needs project config
- THEN tool calls `get_current_session(project_name)`
- AND session provides config via `await session.get_project()`
- AND tool can update config via `await session.update_config()`

#### Scenario: Missing session
- WHEN tool accesses session that doesn't exist
- THEN clear error is raised
- AND error message guides user to create session

### Requirement: Test Configuration Isolation
Tests SHALL achieve configuration isolation through Session constructor parameters rather
than ConfigManager injection.

#### Scenario: Integration test isolation
- **WHEN** integration tests need isolated configuration environments
- **THEN** tests SHALL pass `_config_dir_for_tests` to `get_session()` or `Session` constructor
- **AND** tests SHALL NOT create or inject ConfigManager instances directly

### Requirement: Unified Session Access
The system SHALL provide a single `get_session()` async function that replaces both
`get_or_create_session` and `get_current_session`.

#### Scenario: Signature
- **WHEN** `get_session` is defined
- **THEN** its signature SHALL be `async def get_session(ctx=None, *, project_name=None, _config_dir_for_tests=None) -> Session`
- **AND** it SHALL never return None

#### Scenario: Tool usage
- **WHEN** a tool needs the session
- **THEN** it calls `session = await get_session(ctx)`
- **AND** no separate helper functions are needed

### Requirement: Per-Task File Cache
The system SHALL maintain file cache state per async task using a ContextVar, not as a
module-level singleton.

Each client connection SHALL have its own `FileCache` instance. File content sent by
one agent SHALL NOT be visible to another.

#### Scenario: File cache isolation
- **WHEN** Client A sends file content via `send_file_content`
- **THEN** the content is cached in Client A's task-local FileCache
- **AND** Client B's FileCache does not contain Client A's files

### Requirement: Per-Task Task Manager
The system SHALL maintain a TaskManager instance per async task using a ContextVar, not
as a class-level singleton.

Each client connection SHALL have its own TaskManager with isolated instruction queue,
timer tasks, and event dispatch.

#### Scenario: Task manager isolation
- **WHEN** Client A queues an instruction via the task manager
- **THEN** only Client A receives that instruction
- **AND** Client B's task manager is unaffected

#### Scenario: On-demand creation
- **WHEN** `get_task_manager()` is called and no manager exists in the current task
- **THEN** a new TaskManager is created and stored in the ContextVar

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

### Requirement: Roots Change Handling
The system SHALL handle MCP `roots/list_changed` notifications to detect project switches.

#### Scenario: IDE switches project
- **WHEN** the MCP client sends a `roots/list_changed` notification
- **AND** the new roots resolve to a different project name
- **THEN** the active session calls `switch_project` with the new project name
- **AND** `session.roots` is updated with the new roots list
- **AND** template context cache is invalidated

#### Scenario: Roots change but project unchanged
- **WHEN** the MCP client sends a `roots/list_changed` notification
- **AND** the new roots resolve to the same project name
- **THEN** `session.roots` is updated
- **AND** no project switch occurs

#### Scenario: No active session
- **WHEN** a `roots/list_changed` notification arrives before any session exists
- **THEN** the bootstrap roots ContextVar is updated
- **AND** the next session creation uses the updated roots

