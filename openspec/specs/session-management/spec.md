# session-management Specification

## Purpose
Provides session management with non-singleton sessions, lazy config loading, functional updates, and efficient MCP context caching with deduplication.
## Requirements
### Requirement: Session Non-Singleton
The system SHALL implement Session as a non-singleton class. One Session exists per
client connection. In HTTP transport, each concurrent client has its own Session via
ContextVar task isolation.

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

