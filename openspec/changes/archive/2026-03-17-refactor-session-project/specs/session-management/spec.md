## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: Session Lifecycle Management
The system SHALL maintain a single session for the lifetime of the client connection.

#### Scenario: Session persists across project switches
- **WHEN** the active project is switched via `set_project`
- **THEN** the same Session instance is retained
- **AND** project-scoped data is reloaded on the existing session

#### Scenario: Session cleanup
- **WHEN** the MCP server shuts down or the client disconnects
- **THEN** session resources are released

### Requirement: Test Configuration Isolation
Tests SHALL achieve configuration isolation through Session constructor parameters rather
than ConfigManager injection.

#### Scenario: Integration test isolation
- **WHEN** integration tests need isolated configuration environments
- **THEN** tests SHALL pass `_config_dir_for_tests` to `get_session()` or `Session` constructor
- **AND** tests SHALL NOT create or inject ConfigManager instances directly


