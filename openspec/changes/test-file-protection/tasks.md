# Test File Protection - Tasks

## Phase 1: Setup (2 tasks)

- [x] Add `watchdog` to dev dependency group using `uv add --dev watchdog`
- [x] Verify installation with `uv sync`

## Phase 2: Path Helper Implementation (3 tasks)

- [x] Create `src/mcp_guide/config_paths.py` module
- [x] Implement `get_default_config_file() -> Path` (XDG_CONFIG_HOME support, Windows APPDATA support)
- [x] Implement `get_default_docroot() -> Path` (returns config_file.parent / "docs")

## Phase 3: Copy Existing Test Fixtures (7 tasks)

- [x] Create `tests/conftest.py`
- [x] Copy `pytest_configure()` hook (environment variable isolation)
- [x] Copy `pytest_unconfigure()` hook (cleanup)
- [x] Copy `isolated_config_file` fixture (modified to use `get_default_config_file()`)
- [x] Copy `isolated_session_manager` fixture (modified to remove singleton reset)
- [x] Copy `temp_project_dir` fixture
- [x] Copy `unique_category_name` fixture and `event_loop` fixture

## Phase 4: Add Watchdog Protection (6 tasks)

- [x] Add `ProductionFileHandler(FileSystemEventHandler)` class to conftest.py
- [x] Add `protect_production_files` autouse fixture to conftest.py
- [x] Configure watchdog observer for mcp-guide config path (recursive=False, only if exists)
- [x] Configure watchdog observer for mcp-guide docroot path (recursive=True, only if exists)
- [x] Configure watchdog observer for mcp-server-guide config path (recursive=False, only if exists)
- [x] Configure watchdog observer for mcp-server-guide docroot path (recursive=True, only if exists)

**Note**: Watchdog only monitors paths that exist. If mcp-guide paths don't exist yet (expected), they won't be monitored. If they appear during tests, they won't be caught until next test run - this is acceptable as early warning.

## Phase 5: Validation Tests (5 tasks)

- [x] Create `tests/test_file_protection.py`
- [x] Write test that attempts to modify mcp-guide production config (should terminate immediately, skip if path doesn't exist)
- [x] Write test that attempts to modify mcp-guide production docroot (should terminate immediately, skip if path doesn't exist)
- [x] Write test that attempts to modify mcp-server-guide production config (should terminate immediately, skip if path doesn't exist)
- [x] Write test that attempts to modify mcp-server-guide production docroot (should terminate immediately, skip if path doesn't exist)

**Note**: Tests use `pytest.skip()` if the production path doesn't exist yet. This allows tests to pass in fresh environments while still validating protection when paths exist.

## Phase 6: Documentation (1 task)

- [x] Add module docstring to conftest.py explaining all isolation mechanisms

## Success Criteria

- [x] Watchdog installed as dev dependency
- [x] config_paths module provides XDG-compliant default paths
- [x] All existing isolation fixtures copied from mcp-server-guide
- [x] Environment variables redirected to temp directories before imports
- [x] Watchdog monitors mcp-guide config and docroot (recursive)
- [x] Watchdog monitors mcp-server-guide config and docroot (recursive)
- [x] Tests terminate immediately with clear error on production file modification
- [x] Normal test execution unaffected
