# Test File Protection - Tasks

## Phase 1: Setup (2 tasks)

- [ ] Add `watchdog` to `[project.optional-dependencies]` dev group in pyproject.toml
- [ ] Run `uv sync` to install watchdog

## Phase 2: Path Helper Implementation (3 tasks)

- [ ] Create `src/mcp_guide/config_paths.py` module
- [ ] Implement `get_default_config_file() -> Path` (XDG_CONFIG_HOME support, Windows APPDATA support)
- [ ] Implement `get_default_docroot() -> Path` (returns config_file.parent / "docs")

## Phase 3: Copy Existing Test Fixtures (7 tasks)

- [ ] Create `tests/conftest.py`
- [ ] Copy `pytest_configure()` hook (environment variable isolation)
- [ ] Copy `pytest_unconfigure()` hook (cleanup)
- [ ] Copy `isolated_config_file` fixture (modified to use `get_default_config_file()`)
- [ ] Copy `isolated_session_manager` fixture (modified to remove singleton reset)
- [ ] Copy `temp_project_dir` fixture
- [ ] Copy `unique_category_name` fixture and `event_loop` fixture

## Phase 4: Add Watchdog Protection (4 tasks)

- [ ] Add `ProductionFileHandler(FileSystemEventHandler)` class to conftest.py
- [ ] Add `protect_production_files` autouse fixture to conftest.py
- [ ] Configure watchdog observer for config file path (recursive=False)
- [ ] Configure watchdog observer for docroot path (recursive=True)

## Phase 5: Validation Tests (3 tasks)

- [ ] Create `tests/test_file_protection.py`
- [ ] Write test that attempts to modify production config file (should terminate immediately)
- [ ] Write test that attempts to modify production docroot file (should terminate immediately)

## Phase 6: Documentation (1 task)

- [ ] Add module docstring to conftest.py explaining all isolation mechanisms

## Success Criteria

- [ ] Watchdog installed as dev dependency
- [ ] config_paths module provides XDG-compliant default paths
- [ ] All existing isolation fixtures copied from mcp-server-guide
- [ ] Environment variables redirected to temp directories before imports
- [ ] Watchdog monitors both config file and docroot (recursive)
- [ ] Tests terminate immediately with clear error on production file modification
- [ ] Normal test execution unaffected
