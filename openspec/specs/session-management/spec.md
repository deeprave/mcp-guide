# session-management Specification

## Purpose
Provides session management with non-singleton sessions, lazy config loading, functional updates, and efficient MCP context caching with deduplication.
## Requirements
### Requirement: Session Non-Singleton
The system SHALL implement Session as a non-singleton dataclass.

#### Scenario: Session creation
- WHEN Session is created with project_name
- THEN project name format is validated in `__post_init__`
- AND config_manager reference is stored
- AND mutable SessionState is initialized
- AND multiple sessions can exist for different projects

#### Scenario: Name format validation
- WHEN Session is created with empty or whitespace-only name
- THEN ValueError is raised immediately
- AND session is not created

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
The system SHALL track active sessions per async task using ContextVar.

#### Scenario: Set current session
- WHEN `set_current_session(session)` is called
- THEN session is stored in current async task context
- AND session is retrievable via `get_current_session(project_name)`
- AND session is isolated from other async tasks

#### Scenario: Get current session
- WHEN `get_current_session(project_name)` is called
- THEN session for that project is returned if it exists
- AND None is returned if no session exists
- AND only sessions in current async task are accessible

#### Scenario: Remove current session
- WHEN `remove_current_session(project_name)` is called
- THEN session is removed from current async task context
- AND subsequent get_current_session returns None

#### Scenario: Concurrent sessions
- WHEN multiple async tasks create sessions
- THEN each task has isolated session storage
- AND sessions don't leak between tasks
- AND different projects can have sessions in same task

### Requirement: Session Lifecycle Management
The system SHALL provide clear session lifecycle patterns.

#### Scenario: Session creation and registration
- WHEN a session is created for a tool operation
- THEN session is registered in ContextVar
- AND session is available for nested operations
- AND session is cleaned up after operation

#### Scenario: Session cleanup
- WHEN operation completes
- THEN session is removed from ContextVar
- AND resources are released
- AND no session leaks occur

### Requirement: MCP Context Deduplication
The system SHALL eliminate duplicate MCP context extraction calls using a single comprehensive container.

#### Scenario: Single MCP context container
- WHEN MCP context needs to be cached
- THEN CachedMcpContext dataclass is used containing:
  - roots: Client roots from MCP session
  - project_name: Determined project name
  - agent_info: Detected agent information
  - client_params: MCP client parameters
  - timestamp: Cache timestamp for invalidation
- AND all MCP data is stored in single container
- AND no duplicate data structures exist

#### Scenario: Global context persistence
- WHEN MCP context is cached
- THEN _cached_mcp_context ContextVar stores the context
- AND context persists across project switches
- AND context is isolated per async task
- AND global data is not stored in SessionState

#### Scenario: Consolidated extraction
- WHEN session is created via get_or_create_session()
- THEN _cache_mcp_globals() extracts all MCP context once
- AND tools do NOT call session.cache_mcp_context()
- AND no redundant extraction occurs during tool execution

#### Scenario: Change detection only
- WHEN session.cache_mcp_context() is called
- THEN method only detects if roots have changed
- AND method does NOT perform extraction
- AND extraction is handled by _cache_mcp_globals()

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

