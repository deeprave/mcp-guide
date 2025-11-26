# Session Management Specification

**JIRA**: MG-22
**Epic**: MG-18 - MCP Guide Architectural Reboot

## Purpose

Provide per-project runtime state management with ContextVar for async task-local session tracking.

## ADDED Requirements

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

## Technical Details

### ContextVar Structure
```python
active_sessions: ContextVar[Dict[str, Session]] = ContextVar(
    'active_sessions',
    default={}
)
```

### Session Fields
- `project_name: str` - Project identifier
- `config_manager: ConfigManager` - Config file manager
- `_state: SessionState` - Mutable runtime state
- `_cached_project: Optional[Project]` - Cached config

### Helper Functions
- `get_current_session(project_name: str) -> Optional[Session]`
- `set_current_session(session: Session) -> None`
- `remove_current_session(project_name: str) -> None`

### Concurrency Model
- Each async task has isolated session storage
- ContextVar provides task-local storage
- No locks needed (task-local by design)
- Sessions can be created/destroyed independently

## Dependencies
- contextvars (Python stdlib)
- mcp_guide.models for Project model
- mcp_guide.config for ConfigManager
