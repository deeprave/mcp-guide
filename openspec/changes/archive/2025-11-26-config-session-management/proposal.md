# Proposal: Configuration and Session Management

## Overview

Implement the core architecture for configuration management and session handling as defined in ADR-006 and the v2 architecture specification.

## Motivation

Establish the foundational patterns for managing project configurations and runtime sessions that:
- Separates global concerns (config file) from per-project concerns (session state)
- Supports concurrent operations on different projects via ContextVar
- Provides immutable configuration with functional updates
- Enables testable, explicit session management
- Fixes v1 architectural issues (singleton at wrong level, hidden state, testing complexity)

## Context

This implements the core architecture that all tools will depend on. The design is fully specified in:
- **ADR-006**: Session Management Architecture (detailed design)
- **Architecture Spec**: `openspec/project.md` (high-level principles)

**Prerequisites:**
- Working MCP server (main-entry-point complete)
- FastMCP integration validated
- Testing infrastructure with MCP Inspector

## Objectives

1. Implement ConfigManager singleton for config file management
2. Implement Session non-singleton for per-project runtime state
3. Create immutable Project model with functional updates
4. Integrate ContextVar for async task-local session tracking
5. Provide session access patterns for tools

## Requirements

### ConfigManager (Singleton)

**File**: `src/mcp_guide/config.py`

- Singleton pattern with thread-safe initialization
- Manages single YAML file: `~/.config/mcp-guide/config.yaml`
- Custom async file locking for atomic operations (matches mcp-server-guide pattern)
- Operations:
  - `get_or_create_project_config(name) -> Project`
  - `save_project_config(project: Project) -> None`
  - `rename_project(old, new) -> None`
  - `list_projects() -> List[str]`
  - `delete_project(name) -> None`

### Session (Non-Singleton)

**File**: `src/mcp_guide/session.py`

- Dataclass with project_name, config_manager, state
- Eager name validation in `__post_init__`
- Lazy config loading via `@property project`
- Functional config updates: `update_config(updater: Callable)`
- Mutable state access: `get_state() -> SessionState`

### Immutable Project Model

**File**: `src/mcp_guide/models.py`

- Frozen dataclass with Pydantic validation
- Fields: name, categories, collections, timestamps
- Functional update methods:
  - `with_category(category) -> Project`
  - `without_category(name) -> Project`
  - Similar for collections
- YAML serialization/deserialization

### ContextVar Integration

**File**: `src/mcp_guide/session.py`

- Global ContextVar: `active_sessions: ContextVar[Dict[str, Session]]`
- Helper functions:
  - `get_current_session(project_name) -> Optional[Session]`
  - `set_current_session(session) -> None`
  - `remove_current_session(project_name) -> None`

### Tool Integration Pattern

**File**: `src/mcp_guide/tools/base.py` (or similar)

- Example tool showing session access
- Error handling for missing session
- Result[T] pattern integration

## Implementation Phases

### Phase 1: Models and Config Manager
- [ ] Create immutable Project model (Pydantic)
- [ ] Create Category and Collection models
- [x] Create SessionState model
- [x] Implement ConfigManager singleton
- [x] Add custom async file locking (mcp-server-guide pattern)
- [x] Implement YAML serialization

### Phase 2: Session Management
- [ ] Implement Session dataclass
- [ ] Add eager name validation
- [ ] Add lazy config loading
- [ ] Implement functional update pattern
- [ ] Add state management

### Phase 3: ContextVar Integration
- [ ] Create ContextVar for session tracking
- [ ] Implement session helper functions
- [ ] Add session lifecycle management
- [ ] Test concurrent session access

### Phase 4: Tool Integration
- [ ] Create base tool pattern for session access
- [ ] Implement example tool using sessions
- [ ] Document session access patterns
- [ ] Add error handling for missing sessions

### Phase 5: Testing
- [ ] Unit tests for ConfigManager
- [ ] Unit tests for Session
- [ ] Unit tests for Project model
- [ ] Integration tests for ContextVar
- [ ] Concurrent access tests
- [ ] File locking tests

## Dependencies

**Requires:**
- main-entry-point (working MCP server)
- Result[T] pattern (ADR-003)
- Logging architecture (ADR-004)

**Blocks:**
- All tool implementations
- All prompt implementations
- Resource implementations

## Out of Scope

- Tool implementations (separate changes)
- Prompt implementations (separate changes)
- Migration from v1 (no compatibility layer)
- Multi-process synchronization

## Success Criteria

- [ ] ConfigManager can load/save configs atomically
- [ ] Session can be created for any project
- [ ] ContextVar tracks sessions per async task
- [ ] Concurrent sessions on different projects work correctly
- [ ] Immutable Project updates work functionally
- [ ] All tests pass with ≥90% coverage
- [ ] File locking prevents race conditions
- [ ] Example tool demonstrates session access pattern

## Quality Gates

All quality gates must pass before requesting user approval:

### Test Quality
- [ ] 100% test pass rate (no failures, no skips)
- [ ] No test warnings when run with `-Walways`
- [ ] All tests use isolation fixtures (isolated_config_file, temp_project_dir)
- [ ] Production file protection not triggered during test runs
- [ ] Integration tests verify end-to-end workflows

### Code Coverage
- [ ] ≥90% coverage for models.py
- [ ] ≥90% coverage for config.py
- [ ] ≥90% coverage for session.py
- [ ] All uncovered lines justified or tested

### Type Safety
- [ ] Zero mypy errors in strict mode
- [ ] All public APIs have complete type hints
- [ ] No `type: ignore` comments without justification

### Code Quality
- [ ] Zero ruff linting errors
- [ ] Code formatted with ruff
- [ ] No verbose or unnecessary code
- [ ] No TODO comments in production code
- [ ] No debug print statements

### Concurrency
- [ ] ContextVar provides task isolation (verified by tests)
- [ ] File locking prevents race conditions (verified by tests)
- [ ] Singleton thread-safe (verified by tests)

### Documentation
- [ ] All public classes have docstrings
- [ ] All public methods have docstrings
- [ ] Session access pattern documented with examples
- [ ] Code examples in docstrings are correct

### Dependencies
- [x] No new dependencies required (uses custom file locking)
- [x] Existing dependencies sufficient (Pydantic, PyYAML)

## References

- **ADR-006**: Session Management Architecture (detailed design)
- **Architecture Spec**: `openspec/project.md`
- **ADR-003**: Result Pattern for Tool and Prompt Responses
- **v1 Issues**: Singleton at wrong level, testing complexity, hidden state
