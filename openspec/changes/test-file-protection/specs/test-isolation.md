# Test Isolation Specification

## Overview

This specification documents test isolation measures that prevent tests from interfering with production data or each other. It covers both existing patterns (subprocess isolation) and new protective measures (filesystem monitoring).

## Existing Isolation Measures (To Be Copied from mcp-server-guide)

### 1. Environment Variable Isolation (pytest_configure hook)

**Source**: `../mcp-server-guide/tests/conftest.py`
**Location**: `tests/conftest.py` (to be created)

**Purpose**: Override XDG environment variables before any code imports to redirect all file operations to temporary directories.

```python
def pytest_configure(config):
    """Configure pytest - runs BEFORE any test collection or imports."""
    global _session_temp_dir

    # Create session-wide temp directory
    _session_temp_dir = Path(tempfile.mkdtemp(prefix="mcp_test_session_"))

    # Create isolated config and docs directories
    test_config_dir = _session_temp_dir / "config"
    test_docs_dir = _session_temp_dir / "docs"
    test_config_dir.mkdir(parents=True)
    test_docs_dir.mkdir(parents=True)

    # Create mcp-guide subdirectory for config files
    (test_config_dir / "mcp-guide").mkdir(parents=True, exist_ok=True)

    # Override environment variables BEFORE any imports
    os.environ["HOME"] = str(_session_temp_dir)
    os.environ["XDG_CONFIG_HOME"] = str(test_config_dir)
    os.environ["XDG_DATA_HOME"] = str(test_docs_dir)

    # Windows support
    if os.name == "nt":
        os.environ["APPDATA"] = str(test_config_dir)
        os.environ["LOCALAPPDATA"] = str(test_config_dir)
```

**Critical Timing**: This hook runs BEFORE test collection and imports, ensuring production code that caches paths at import time uses test directories.

**Cleanup**: `pytest_unconfigure()` hook removes temp directory after all tests complete.

### 2. Isolated Config File Fixture

**Source**: `../mcp-server-guide/tests/conftest.py` (modified for mcp-guide)
**Location**: `tests/conftest.py` (to be created)

**Purpose**: Provide test-specific config file path for tests that need real file I/O.

**Note**: Modified from mcp-server-guide to use `get_default_config_file()` instead of `os.getcwd()` to ensure it uses the XDG-redirected path set by `pytest_configure()`.

```python
@pytest.fixture
def isolated_config_file():
    """Provide an isolated config file path for tests that need real file I/O."""
    from mcp_guide.config_paths import get_default_config_file

    config_path = get_default_config_file()

    if config_path.exists():
        config_path.unlink()

    yield config_path

    if config_path.exists():
        config_path.unlink()
```

**Rationale**: Using `get_default_config_file()` ensures the fixture uses the XDG-redirected path from `pytest_configure()`, avoiding the trap of relying on current working directory.

**Usage**: Tests call `SessionManager()._set_config_filename(isolated_config_file)` to use test-local file.

### 3. Isolated Session Manager Fixture

**Source**: `../mcp-server-guide/tests/conftest.py` (modified for mcp-guide)
**Location**: `tests/conftest.py` (to be created)

**Purpose**: Provide SessionManager with isolated config file.

**Note**: Modified from mcp-server-guide to remove singleton reset logic since mcp-guide does not use singleton pattern.

```python
@pytest.fixture
def isolated_session_manager(isolated_config_file):
    """Provide a SessionManager with isolated config file."""
    manager = SessionManager()
    manager._set_config_filename(isolated_config_file)
    isolated_config_file.parent.mkdir(parents=True, exist_ok=True)

    yield manager
```

### 4. Temporary Project Directory Fixture

**Source**: `../mcp-server-guide/tests/conftest.py`
**Location**: `tests/conftest.py` (to be created)

**Purpose**: Provide unique temporary directory for each test within session temp dir.

```python
@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Provide temporary project directory for tests."""
    import uuid

    global _session_temp_dir

    project_subdir = _session_temp_dir / f"project_{uuid.uuid4().hex[:8]}"
    project_subdir.mkdir(parents=True, exist_ok=True)

    yield project_subdir
```

### 5. Unique Category Name Fixture

**Source**: `../mcp-server-guide/tests/conftest.py`
**Location**: `tests/conftest.py` (to be created)

**Purpose**: Generate unique category names to prevent test conflicts.

```python
@pytest.fixture
def unique_category_name(request):
    """Generate a unique category name for each test."""
    test_id = request.node.nodeid
    hash_val = hashlib.md5(test_id.encode()).hexdigest()[:8]
    return f"cat_{hash_val}"
```

### 6. Event Loop Fixture

**Source**: `../mcp-server-guide/tests/conftest.py`
**Location**: `tests/conftest.py` (to be created)

**Purpose**: Provide session-scoped event loop for async tests.

```python
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
```

### 7. Subprocess Integration Tests (Already Implemented)

**Location**: `tests/integration/test_server_startup.py`

**Purpose**: Integration testing of CLI entry point and server startup (not for isolation).

**Note**: This pattern tests the full stack (CLI → entry point → server) but is not part of the isolation strategy. It's documented here for completeness but serves a different purpose than the isolation fixtures above.

```python
@pytest.fixture
async def server_process() -> AsyncIterator[subprocess.Popen]:
    """Start the MCP server process for integration testing."""
    process = subprocess.Popen(
        ["uv", "run", "mcp-guide"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    yield process

    # Cleanup: terminate gracefully, kill if necessary
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
```

**Benefits**:
- Tests actual CLI entry point
- Verifies end-to-end server startup
- Each test gets fresh server process

**Isolation Note**: This provides process isolation for integration tests, but the primary isolation mechanism is the environment variable redirection in `pytest_configure()`.

## New Isolation Measures (To Be Implemented)

### 2. Production File Protection via Filesystem Monitoring

**Location**: `tests/conftest.py` (to be created)

**Purpose**: Prevent any test from accidentally modifying production configuration or documents.

#### Protected Paths

1. **Production Config Directory**: `$XDG_CONFIG_HOME/mcp-guide/` (or `~/.config/mcp-guide/`)
   - Contains: `config.json` and related configuration files
   - Monitoring: Non-recursive (directory level only)
   - Reason: Protects user project configurations

2. **Production Document Root**: `{config_dir}/docs/`
   - Contains: All user documentation, category directories, `__docs__/` folders, metadata
   - Monitoring: Recursive (all subdirectories and files)
   - Reason: Protects all indexed documentation

#### Implementation Pattern

```python
import pytest
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from mcp_guide.config_paths import get_default_config_file, get_default_docroot


class ProductionFileHandler(FileSystemEventHandler):
    """Handler that terminates tests immediately on production file modification."""

    def on_any_event(self, event):
        """Terminate test session if production file is touched."""
        pytest.exit(
            f"PRODUCTION FILE MODIFIED: {event.src_path}\n"
            f"Event type: {event.event_type}\n"
            f"Tests must use temporary directories for file operations.",
            returncode=1
        )


@pytest.fixture(scope="session", autouse=True)
def protect_production_files():
    """Monitor production paths and terminate tests if modified."""
    handler = ProductionFileHandler()
    observer = Observer()

    # Monitor config directory
    config_path = get_default_config_file().parent
    if config_path.exists():
        observer.schedule(handler, str(config_path), recursive=False)

    # Monitor docroot (recursive)
    docroot_path = get_default_docroot()
    if docroot_path.exists():
        observer.schedule(handler, str(docroot_path), recursive=True)

    observer.start()
    yield
    observer.stop()
    observer.join()
```

**Behavior**:
- **Scope**: Session-level, applies to all tests automatically (`autouse=True`)
- **Trigger**: Any filesystem event (create, modify, delete, move) on protected paths
- **Action**: Immediate test termination via `pytest.exit()`
- **Error Message**: Shows exact file path and event type
- **Conditional**: Only monitors paths that exist (handles fresh environments)

#### Benefits

- **Immediate Feedback**: Test stops instantly when production file is touched
- **Clear Errors**: Developer sees exactly which file was modified
- **Zero Production Code Impact**: No test-specific logic in production modules
- **Comprehensive**: Catches all filesystem operations (not just writes)
- **Automatic**: No manual fixture application needed

#### Test Validation

Tests in `tests/test_file_protection.py` will verify:
1. Attempting to write to production config terminates test
2. Attempting to write to production docroot terminates test
3. Normal tests using temporary directories pass without triggering protection

## Integration of Isolation Measures

### Unit Tests
- No special isolation needed (pure functions, no I/O)
- Use standard pytest patterns

### Integration Tests
- **Subprocess isolation**: Each test gets fresh server process
- **File protection**: Watchdog prevents production file access
- **Temporary directories**: Tests should use `tmp_path` fixture for file operations

### Future: Config/Document Tests
When implementing `ProjectConfigManager` and document operations:
- Use `tmp_path` fixture for test-specific config/document directories
- Pass temporary paths via constructor injection (e.g., `config_dir` parameter)
- Never use default paths in tests
- Watchdog protection provides safety net if test setup is incorrect

## Dependencies

- **pytest**: Fixture system, `pytest.exit()`
- **watchdog**: Filesystem monitoring
- **mcp_guide.config_paths**: Production path resolution

## Success Criteria

- [ ] All tests use subprocess isolation or temporary directories
- [ ] Production files protected by watchdog monitoring
- [ ] Tests terminate immediately on production file access
- [ ] Clear error messages guide developers to fix test isolation issues
- [ ] No test-specific code in production modules
- [ ] Environment variables redirect all file operations to temp directories
- [ ] No singleton pattern in mcp-guide (unlike mcp-server-guide)
