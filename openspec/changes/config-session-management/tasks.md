# Tasks: Configuration and Session Management

## Phase 1: Models and Config Manager (TDD)

### 1.1 Immutable Project Model

- [x] 1.1.1 RED: Write test for Project frozen dataclass
- [x] 1.1.2 RED: Write test for Project.with_category() returns new instance
- [x] 1.1.3 RED: Write test for Project.without_category() returns new instance
- [x] 1.1.4 GREEN: Create `src/mcp_guide/models.py` with Project model
- [x] 1.1.5 GREEN: Implement functional update methods
- [x] 1.1.6 REFACTOR: Add Pydantic validation and type hints

### 1.2 Category and Collection Models

- [x] 1.2.1 RED: Write tests for Category model
- [x] 1.2.2 RED: Write tests for Collection model
- [x] 1.2.3 GREEN: Implement Category and Collection in models.py
- [x] 1.2.4 REFACTOR: Add validation rules and constraints

### 1.3 SessionState Model

- [x] 1.3.1 RED: Write tests for SessionState (mutable)
- [x] 1.3.2 GREEN: Implement SessionState dataclass
- [x] 1.3.3 REFACTOR: Add state management methods

### 1.4 ConfigManager Singleton

- [x] 1.4.1 RED: Write test that ConfigManager is singleton
- [x] 1.4.2 RED: Write test for config file initialization
- [x] 1.4.3 GREEN: Create `src/mcp_guide/config.py` with singleton pattern
- [x] 1.4.4 GREEN: Implement __new__ and __init__ with _initialized flag
- [x] 1.4.5 REFACTOR: Add config file path resolution

### 1.5 File Locking

- [x] 1.5.1 RED: Write test for atomic file operations
- [x] 1.5.2 RED: Write test for concurrent access prevention
- [x] 1.5.3 GREEN: Add filelock dependency
- [x] 1.5.4 GREEN: Implement file locking in config manager
- [x] 1.5.5 REFACTOR: Add lock timeout and error handling

### 1.6 YAML Serialization

- [x] 1.6.1 RED: Write test for Project to YAML
- [x] 1.6.2 RED: Write test for YAML to Project
- [x] 1.6.3 GREEN: Implement to_yaml() and from_yaml() methods
- [x] 1.6.4 REFACTOR: Handle nested objects and timestamps

### 1.7 Config Manager Operations

- [x] 1.7.1 RED: Write test for get_or_create_project_config()
- [x] 1.7.2 RED: Write test for save_project_config()
- [x] 1.7.3 RED: Write test for list_projects()
- [x] 1.7.4 GREEN: Implement get_or_create_project_config()
- [x] 1.7.5 GREEN: Implement save_project_config()
- [x] 1.7.6 GREEN: Implement list_projects()
- [x] 1.7.7 REFACTOR: Add error handling with Result[T]

### 1.8 Additional Config Operations

- [x] 1.8.1 RED: Write test for rename_project()
- [x] 1.8.2 RED: Write test for delete_project()
- [x] 1.8.3 GREEN: Implement rename_project()
- [x] 1.8.4 GREEN: Implement delete_project()
- [x] 1.8.5 REFACTOR: Add validation and error messages

## Phase 2: Session Management (TDD)

### 2.1 Session Dataclass

- [x] 2.1.1 RED: Write test for Session creation
- [x] 2.1.2 RED: Write test for project_name validation
- [x] 2.1.3 GREEN: Create `src/mcp_guide/session.py` with Session
- [x] 2.1.4 GREEN: Implement __post_init__ with name validation
- [x] 2.1.5 REFACTOR: Add type hints and docstrings

### 2.2 Lazy Config Loading

- [x] 2.2.1 RED: Write test that project property loads config lazily
- [x] 2.2.2 RED: Write test that project is cached after first access
- [x] 2.2.3 GREEN: Implement @property project with lazy loading
- [x] 2.2.4 REFACTOR: Add error handling for missing projects

### 2.3 Functional Config Updates

- [x] 2.3.1 RED: Write test for update_config() with lambda
- [x] 2.3.2 RED: Write test that update_config() saves to file
- [x] 2.3.3 RED: Write test that update_config() updates cached project
- [x] 2.3.4 GREEN: Implement update_config() method
- [x] 2.3.5 REFACTOR: Add error handling and logging

### 2.4 State Management

- [x] 2.4.1 RED: Write test for get_state() returns SessionState
- [x] 2.4.2 RED: Write test that state is mutable
- [x] 2.4.3 GREEN: Implement get_state() method
- [x] 2.4.4 REFACTOR: Document state vs config separation

## Phase 3: ContextVar Integration (TDD)

### 3.1 ContextVar Setup

- [x] 3.1.1 RED: Write test for active_sessions ContextVar
- [x] 3.1.2 GREEN: Create active_sessions ContextVar in session.py
- [x] 3.1.3 REFACTOR: Add type hints for Dict[str, Session]

### 3.2 Session Helper Functions

- [x] 3.2.1 RED: Write test for get_current_session()
- [x] 3.2.2 RED: Write test for set_current_session()
- [x] 3.2.3 RED: Write test for remove_current_session()
- [x] 3.2.4 GREEN: Implement get_current_session()
- [x] 3.2.5 GREEN: Implement set_current_session()
- [x] 3.2.6 GREEN: Implement remove_current_session()
- [x] 3.2.7 REFACTOR: Add error handling and validation

### 3.3 Concurrent Session Tests

- [x] 3.3.1 RED: Write test for multiple sessions in different tasks
- [x] 3.3.2 RED: Write test for session isolation between tasks
- [x] 3.3.3 GREEN: Verify ContextVar provides isolation
- [x] 3.3.4 REFACTOR: Add integration test with asyncio.gather()

### 3.4 Session Lifecycle

- [x] 3.4.1 RED: Write test for session creation and registration
- [x] 3.4.2 RED: Write test for session cleanup
- [x] 3.4.3 GREEN: Implement session lifecycle helpers
- [x] 3.4.4 REFACTOR: Add context manager support

## Phase 4: Tool Integration (TDD)

### 4.1 Base Tool Pattern

- [x] 4.1.1 RED: Write test for tool accessing session
- [x] 4.1.2 RED: Write test for tool with missing session
- [x] 4.1.3 GREEN: Create example tool in `src/mcp_guide/tools/example.py`
- [x] 4.1.4 GREEN: Implement session access pattern
- [x] 4.1.5 REFACTOR: Extract common pattern to helper

### 4.2 Error Handling

- [x] 4.2.1 RED: Write test for Result.failure on missing session
- [x] 4.2.2 RED: Write test for Result.failure on invalid project
- [x] 4.2.3 GREEN: Implement error handling with Result[T]
- [x] 4.2.4 REFACTOR: Add descriptive error messages

### 4.3 Documentation

- [x] 4.3.1 Document session access pattern for tools
- [x] 4.3.2 Add code examples to docstrings
- [x] 4.3.3 Create developer guide for session usage

## Phase 5: Integration and Verification

### 5.1 Integration Tests

- [x] 5.1.1 Create `tests/integration/test_config_session.py`
- [x] 5.1.2 Test end-to-end: create session, update config, save
- [x] 5.1.3 Test concurrent sessions on different projects
- [x] 5.1.4 Test file locking prevents race conditions

### 5.2 Coverage and Quality

- [x] 5.2.1 Run pytest with coverage: `uv run pytest --cov`
- [x] 5.2.2 Verify ≥90% coverage for config.py and session.py
- [x] 5.2.3 Run type checking: `uv run mypy src`
- [x] 5.2.4 Run linting: `uv run ruff check src tests`

### 5.3 Performance Tests

- [x] 5.3.1 Test config load/save performance
- [x] 5.3.2 Test concurrent session creation
- [x] 5.3.3 Test file locking overhead

### 5.4 Final Verification

- [x] 5.4.1 All tests pass (100% pass rate)
- [x] 5.4.2 No type errors
- [x] 5.4.3 No linting warnings
- [x] 5.4.4 Documentation complete
- [x] 5.4.5 Ready for tool implementations

## Phase 6: Quality Checks and Verification

### 6.1 Test Suite Execution

- [x] 6.1.1 Run all tests: `uv run pytest -v`
- [x] 6.1.2 Verify 100% test pass rate (no failures, no skips)
- [x] 6.1.3 Run tests with warnings: `uv run pytest -v -Walways`
- [x] 6.1.4 Verify no warnings emitted
- [x] 6.1.5 Verify test isolation fixtures used in all config/session tests
- [x] 6.1.6 Verify production file protection not triggered

### 6.2 Code Coverage

- [x] 6.2.1 Run coverage: `uv run pytest --cov=src/mcp_guide --cov-report=term-missing`
- [x] 6.2.2 Verify ≥90% coverage for `src/mcp_guide/models.py`
- [x] 6.2.3 Verify ≥90% coverage for `src/mcp_guide/config.py`
- [x] 6.2.4 Verify ≥90% coverage for `src/mcp_guide/session.py`
- [x] 6.2.5 Review uncovered lines and justify or add tests

### 6.3 Type Checking

- [x] 6.3.1 Run mypy: `uv run mypy src`
- [x] 6.3.2 Verify no type errors
- [x] 6.3.3 Verify strict mode compliance
- [x] 6.3.4 Check all public APIs have type hints

### 6.4 Code Quality

- [x] 6.4.1 Run linting: `uv run ruff check src tests`
- [x] 6.4.2 Verify no linting errors
- [x] 6.4.3 Run formatting check: `uv run ruff format --check src tests`
- [x] 6.4.4 Verify code is formatted
- [x] 6.4.5 Review code for minimal implementation (no verbose code)

### 6.5 Concurrency and Thread Safety

- [x] 6.5.1 Run concurrent session tests
- [x] 6.5.2 Verify ContextVar provides task isolation
- [x] 6.5.3 Run file locking tests
- [x] 6.5.4 Verify no race conditions in config file access
- [x] 6.5.5 Test singleton thread safety

### 6.6 Integration Verification

- [x] 6.6.1 Run integration tests: `uv run pytest tests/integration/`
- [x] 6.6.2 Verify end-to-end workflow works
- [x] 6.6.3 Test with isolated_config_file fixture
- [x] 6.6.4 Verify no production file access during tests

### 6.7 Documentation Review

- [x] 6.7.1 Verify all public classes have docstrings
- [x] 6.7.2 Verify all public methods have docstrings
- [x] 6.7.3 Review code examples in docstrings
- [x] 6.7.4 Verify session access pattern documented

### 6.8 Dependency Check

- [x] 6.8.1 Verify filelock added to pyproject.toml
- [x] 6.8.2 Run `uv lock` to update lockfile
- [x] 6.8.3 Verify no unnecessary dependencies added

### 6.9 Final Checklist

- [x] 6.9.1 All 116 tasks marked complete
- [x] 6.9.2 All success criteria met (from proposal.md)
- [x] 6.9.3 No TODO comments in production code
- [x] 6.9.4 No debug print statements
- [x] 6.9.5 All tests use proper fixtures (isolated_config_file, etc.)
- [x] 6.9.6 Production file protection verified working

### 6.10 Review and Approval

- [x] 6.10.1 **READY FOR REVIEW** - Request user review
- [x] 6.10.2 Address review concerns (if any)
- [x] 6.10.3 Re-run quality checks after changes
- [x] 6.10.4 **USER APPROVAL RECEIVED** - Ready for archiving
