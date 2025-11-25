# Tasks: Configuration and Session Management

## Phase 1: Models and Config Manager (TDD)

### 1.1 Immutable Project Model

- [ ] 1.1.1 RED: Write test for Project frozen dataclass
- [ ] 1.1.2 RED: Write test for Project.with_category() returns new instance
- [ ] 1.1.3 RED: Write test for Project.without_category() returns new instance
- [ ] 1.1.4 GREEN: Create `src/mcp_guide/models.py` with Project model
- [ ] 1.1.5 GREEN: Implement functional update methods
- [ ] 1.1.6 REFACTOR: Add Pydantic validation and type hints

### 1.2 Category and Collection Models

- [ ] 1.2.1 RED: Write tests for Category model
- [ ] 1.2.2 RED: Write tests for Collection model
- [ ] 1.2.3 GREEN: Implement Category and Collection in models.py
- [ ] 1.2.4 REFACTOR: Add validation rules and constraints

### 1.3 SessionState Model

- [ ] 1.3.1 RED: Write tests for SessionState (mutable)
- [ ] 1.3.2 GREEN: Implement SessionState dataclass
- [ ] 1.3.3 REFACTOR: Add state management methods

### 1.4 ProjectConfigManager Singleton

- [ ] 1.4.1 RED: Write test that ProjectConfigManager is singleton
- [ ] 1.4.2 RED: Write test for config file initialization
- [ ] 1.4.3 GREEN: Create `src/mcp_guide/config.py` with singleton pattern
- [ ] 1.4.4 GREEN: Implement __new__ and __init__ with _initialized flag
- [ ] 1.4.5 REFACTOR: Add config file path resolution

### 1.5 File Locking

- [ ] 1.5.1 RED: Write test for atomic file operations
- [ ] 1.5.2 RED: Write test for concurrent access prevention
- [ ] 1.5.3 GREEN: Add filelock dependency
- [ ] 1.5.4 GREEN: Implement file locking in config manager
- [ ] 1.5.5 REFACTOR: Add lock timeout and error handling

### 1.6 YAML Serialization

- [ ] 1.6.1 RED: Write test for Project to YAML
- [ ] 1.6.2 RED: Write test for YAML to Project
- [ ] 1.6.3 GREEN: Implement to_yaml() and from_yaml() methods
- [ ] 1.6.4 REFACTOR: Handle nested objects and timestamps

### 1.7 Config Manager Operations

- [ ] 1.7.1 RED: Write test for get_or_create_project_config()
- [ ] 1.7.2 RED: Write test for save_project_config()
- [ ] 1.7.3 RED: Write test for list_projects()
- [ ] 1.7.4 GREEN: Implement get_or_create_project_config()
- [ ] 1.7.5 GREEN: Implement save_project_config()
- [ ] 1.7.6 GREEN: Implement list_projects()
- [ ] 1.7.7 REFACTOR: Add error handling with Result[T]

### 1.8 Additional Config Operations

- [ ] 1.8.1 RED: Write test for rename_project()
- [ ] 1.8.2 RED: Write test for delete_project()
- [ ] 1.8.3 GREEN: Implement rename_project()
- [ ] 1.8.4 GREEN: Implement delete_project()
- [ ] 1.8.5 REFACTOR: Add validation and error messages

## Phase 2: Session Management (TDD)

### 2.1 GuideSession Dataclass

- [ ] 2.1.1 RED: Write test for GuideSession creation
- [ ] 2.1.2 RED: Write test for project_name validation
- [ ] 2.1.3 GREEN: Create `src/mcp_guide/session.py` with GuideSession
- [ ] 2.1.4 GREEN: Implement __post_init__ with name validation
- [ ] 2.1.5 REFACTOR: Add type hints and docstrings

### 2.2 Lazy Config Loading

- [ ] 2.2.1 RED: Write test that project property loads config lazily
- [ ] 2.2.2 RED: Write test that project is cached after first access
- [ ] 2.2.3 GREEN: Implement @property project with lazy loading
- [ ] 2.2.4 REFACTOR: Add error handling for missing projects

### 2.3 Functional Config Updates

- [ ] 2.3.1 RED: Write test for update_config() with lambda
- [ ] 2.3.2 RED: Write test that update_config() saves to file
- [ ] 2.3.3 RED: Write test that update_config() updates cached project
- [ ] 2.3.4 GREEN: Implement update_config() method
- [ ] 2.3.5 REFACTOR: Add error handling and logging

### 2.4 State Management

- [ ] 2.4.1 RED: Write test for get_state() returns SessionState
- [ ] 2.4.2 RED: Write test that state is mutable
- [ ] 2.4.3 GREEN: Implement get_state() method
- [ ] 2.4.4 REFACTOR: Document state vs config separation

## Phase 3: ContextVar Integration (TDD)

### 3.1 ContextVar Setup

- [ ] 3.1.1 RED: Write test for active_sessions ContextVar
- [ ] 3.1.2 GREEN: Create active_sessions ContextVar in session.py
- [ ] 3.1.3 REFACTOR: Add type hints for Dict[str, GuideSession]

### 3.2 Session Helper Functions

- [ ] 3.2.1 RED: Write test for get_current_session()
- [ ] 3.2.2 RED: Write test for set_current_session()
- [ ] 3.2.3 RED: Write test for remove_current_session()
- [ ] 3.2.4 GREEN: Implement get_current_session()
- [ ] 3.2.5 GREEN: Implement set_current_session()
- [ ] 3.2.6 GREEN: Implement remove_current_session()
- [ ] 3.2.7 REFACTOR: Add error handling and validation

### 3.3 Concurrent Session Tests

- [ ] 3.3.1 RED: Write test for multiple sessions in different tasks
- [ ] 3.3.2 RED: Write test for session isolation between tasks
- [ ] 3.3.3 GREEN: Verify ContextVar provides isolation
- [ ] 3.3.4 REFACTOR: Add integration test with asyncio.gather()

### 3.4 Session Lifecycle

- [ ] 3.4.1 RED: Write test for session creation and registration
- [ ] 3.4.2 RED: Write test for session cleanup
- [ ] 3.4.3 GREEN: Implement session lifecycle helpers
- [ ] 3.4.4 REFACTOR: Add context manager support

## Phase 4: Tool Integration (TDD)

### 4.1 Base Tool Pattern

- [ ] 4.1.1 RED: Write test for tool accessing session
- [ ] 4.1.2 RED: Write test for tool with missing session
- [ ] 4.1.3 GREEN: Create example tool in `src/mcp_guide/tools/example.py`
- [ ] 4.1.4 GREEN: Implement session access pattern
- [ ] 4.1.5 REFACTOR: Extract common pattern to helper

### 4.2 Error Handling

- [ ] 4.2.1 RED: Write test for Result.failure on missing session
- [ ] 4.2.2 RED: Write test for Result.failure on invalid project
- [ ] 4.2.3 GREEN: Implement error handling with Result[T]
- [ ] 4.2.4 REFACTOR: Add descriptive error messages

### 4.3 Documentation

- [ ] 4.3.1 Document session access pattern for tools
- [ ] 4.3.2 Add code examples to docstrings
- [ ] 4.3.3 Create developer guide for session usage

## Phase 5: Integration and Verification

### 5.1 Integration Tests

- [ ] 5.1.1 Create `tests/integration/test_config_session.py`
- [ ] 5.1.2 Test end-to-end: create session, update config, save
- [ ] 5.1.3 Test concurrent sessions on different projects
- [ ] 5.1.4 Test file locking prevents race conditions

### 5.2 Coverage and Quality

- [ ] 5.2.1 Run pytest with coverage: `uv run pytest --cov`
- [ ] 5.2.2 Verify ≥90% coverage for config.py and session.py
- [ ] 5.2.3 Run type checking: `uv run mypy src`
- [ ] 5.2.4 Run linting: `uv run ruff check src tests`

### 5.3 Performance Tests

- [ ] 5.3.1 Test config load/save performance
- [ ] 5.3.2 Test concurrent session creation
- [ ] 5.3.3 Test file locking overhead

### 5.4 Final Verification

- [ ] 5.4.1 All tests pass (100% pass rate)
- [ ] 5.4.2 No type errors
- [ ] 5.4.3 No linting warnings
- [ ] 5.4.4 Documentation complete
- [ ] 5.4.5 Ready for tool implementations

## Phase 6: Check Phase

- [ ] 6.1 Run all tests: `uv run pytest`
- [ ] 6.2 Verify 100% test pass rate
- [ ] 6.3 Run type checking: `uv run mypy src`
- [ ] 6.4 Verify no type errors
- [ ] 6.5 Run linting: `uv run ruff check src tests`
- [ ] 6.6 Verify no linting warnings
- [ ] 6.7 Verify coverage ≥90%: `uv run pytest --cov`
- [ ] 6.8 Test concurrent session access
- [ ] 6.9 Test file locking prevents race conditions
- [ ] 6.10 Review all tasks marked complete
- [ ] 6.11 **READY FOR REVIEW** - Request user review
- [ ] 6.12 Address review concerns (if any)
- [ ] 6.13 **USER APPROVAL RECEIVED** - Ready for archiving
