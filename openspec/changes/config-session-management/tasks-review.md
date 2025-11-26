# Code Review: Config and Session Management Implementation

## Summary
The implementation successfully delivers the core functionality for config and session management with good test coverage (87% overall, 95%+ for critical modules). All tests pass, type checking is clean, and linting shows no issues. However, there are several **critical issues** that must be addressed before this can be considered production-ready, primarily around the singleton pattern implementation, missing constructor injection for testing, and incomplete validation.

## Critical Issues (5)

### 1. Missing Constructor Injection for Testing
**critical (bug_risk, testability)**

**File**: `src/mcp_guide/config.py:20-26`

**Location(s)**:
- `src/mcp_guide/config.py:20-26`

**Context**:
```python
class ConfigManager:
    """Singleton manager for project configuration file."""

    _instance: Optional["ConfigManager"] = None
    _lock = asyncio.Lock()
    _initialized = False

    def __new__(cls) -> "ConfigManager":
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**Comments**:
The spec explicitly requires "Constructor Injection for Testing" with a `config_dir` parameter to support test isolation. The current implementation has NO way to inject a custom config directory, making it impossible to properly isolate tests without relying on environment variable manipulation.

**Spec Requirement**:
> ### Requirement: Constructor Injection for Testing
> The system SHALL support config_dir parameter for test isolation.
>
> #### Scenario: Test isolation
> - WHEN ConfigManager is created with config_dir parameter
> - THEN config file is located in specified directory
> - AND production config is not accessed
> - AND tests can use temporary directories

**Impact**:
- Tests currently rely on `pytest_configure` hook to override environment variables BEFORE imports
- This is fragile and doesn't allow per-test isolation
- The `isolated_config_file` fixture exists but ConfigManager ignores it
- Tests work by accident (environment manipulation) rather than by design

**Suggested Fix**:
```python
class ConfigManager:
    """Singleton manager for project configuration file."""

    _instances: dict[Optional[str], "ConfigManager"] = {}
    _lock = asyncio.Lock()

    def __new__(cls, config_dir: Optional[str] = None) -> "ConfigManager":
        """Ensure only one instance exists per config_dir."""
        if config_dir not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[config_dir] = instance
            instance._initialized = False
            instance._config_dir = config_dir
        return cls._instances[config_dir]

    async def _ensure_initialized(self) -> None:
        """Initialize config manager (only once)."""
        if not self._initialized:
            async with self._lock:
                if not self._initialized:
                    from mcp_guide.config_paths import get_config_file
                    self.config_file = get_config_file(self._config_dir)
                    self.config_file.parent.mkdir(parents=True, exist_ok=True)
                    if not self.config_file.exists():
                        self.config_file.write_text("projects: {}\n")
                    self._initialized = True
```

This allows `ConfigManager(config_dir="/tmp/test")` for test isolation while maintaining singleton behavior per config directory.

---

### 2. Singleton Pattern is NOT Thread-Safe
**critical (bug_risk, concurrency)**

**File**: `src/mcp_guide/config.py:20-26`

**Location(s)**:
- `src/mcp_guide/config.py:20-26`

**Context**:
```python
def __new__(cls) -> "ConfigManager":
    """Ensure only one instance exists."""
    if cls._instance is None:
        cls._instance = super().__new__(cls)
    return cls._instance
```

**Comments**:
The spec requires "thread-safe singleton" with "double-checked locking", but the current `__new__` implementation has a classic race condition. Two threads can simultaneously check `cls._instance is None`, both see `None`, and both create instances.

**Spec Requirement**:
> ### Thread Safety
> - Singleton initialization uses double-checked locking
> - File operations protected by file locks
> - No shared mutable state

**Impact**:
- Multiple ConfigManager instances can be created under concurrent access
- This violates the singleton contract
- Could lead to inconsistent state if different instances are used

**Suggested Fix**:
```python
import threading

class ConfigManager:
    """Singleton manager for project configuration file."""

    _instance: Optional["ConfigManager"] = None
    _init_lock = threading.Lock()  # Thread lock for initialization
    _async_lock = asyncio.Lock()   # Async lock for operations
    _initialized = False

    def __new__(cls, config_dir: Optional[str] = None) -> "ConfigManager":
        """Ensure only one instance exists (thread-safe)."""
        # First check (no lock)
        if cls._instance is None:
            # Acquire lock for initialization
            with cls._init_lock:
                # Second check (with lock) - double-checked locking
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._config_dir = config_dir
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance
```

---

### 3. Missing Validation in Models
**critical (bug_risk, data_integrity)**

**File**: `src/mcp_guide/models.py:15-30, 33-48, 51-68`

**Location(s)**:
- `src/mcp_guide/models.py:20` (Category.patterns not validated)
- `src/mcp_guide/models.py:19` (Category.dir not validated)
- `src/mcp_guide/models.py:36` (Collection.categories not validated)

**Context**:
```python
@pydantic_dataclass(frozen=True)
class Category:
    """Category configuration."""

    name: str
    dir: str
    patterns: list[str]

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        import re
        if not re.match(NAME_PATTERN, v):
            raise ValueError(f"Category name must contain only alphanumeric characters, underscores, and hyphens")
        return v
```

**Comments**:
The spec requires validation for patterns (non-empty) and directory (valid path), but these are not implemented. This allows invalid data to be created and persisted.

**Spec Requirements**:
> ### Requirement: Category Model
> #### Scenario: Category validation
> - THEN name is validated (alphanumeric, hyphens, underscores)
> - AND directory path is validated
> - AND patterns list is validated (non-empty)

> ### Validation Rules
> - Patterns: non-empty list of glob patterns
> - Directory: valid path string

**Impact**:
- Empty patterns list can be created, breaking glob matching
- Invalid directory paths can be stored
- Collection can reference non-existent categories
- Data integrity issues will surface later in the system

**Suggested Fix**:
```python
@pydantic_dataclass(frozen=True)
class Category:
    """Category configuration."""

    name: str
    dir: str
    patterns: list[str]

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        import re
        if not re.match(NAME_PATTERN, v):
            raise ValueError(f"Category name must contain only alphanumeric characters, underscores, and hyphens")
        return v

    @field_validator("patterns")
    @classmethod
    def validate_patterns(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Patterns list cannot be empty")
        if not all(isinstance(p, str) and p.strip() for p in v):
            raise ValueError("All patterns must be non-empty strings")
        return v

    @field_validator("dir")
    @classmethod
    def validate_dir(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Directory path cannot be empty")
        # Note: We don't validate if path exists, just that it's a valid string
        return v
```

---

### 4. Incomplete Error Handling in ConfigManager
**critical (bug_risk, reliability)**

**File**: `src/mcp_guide/config.py:52-69, 71-82`

**Location(s)**:
- `src/mcp_guide/config.py:52-69` (get_or_create_project_config)
- `src/mcp_guide/config.py:71-82` (save_project_config)
- All CRUD operations

**Context**:
```python
async def get_or_create_project_config(self, name: str) -> Project:
    """Get project config or create if it doesn't exist."""
    await self._ensure_initialized()

    async def _get_or_create(file_path: Path) -> Project:
        data = yaml.safe_load(file_path.read_text())
        projects = data.get("projects", {})

        if name in projects:
            project_data = projects[name]
            return Project(**project_data)

        # Create new project
        project = Project(name=name)
        projects[name] = self._project_to_dict(project)
        data["projects"] = projects
        file_path.write_text(yaml.dump(data))
        return project

    return await lock_update(self.config_file, _get_or_create)
```

**Comments**:
The spec requires specific error handling for invalid project names, file system errors, and YAML parsing errors. None of these are implemented. All exceptions will bubble up as generic errors.

**Spec Requirements**:
> ### Requirement: Error Handling
> #### Scenario: Invalid project name
> - WHEN operation uses invalid project name
> - THEN ValueError is raised with clear message
>
> #### Scenario: File system errors
> - WHEN config file cannot be read/written
> - THEN IOError is raised with clear message
> - AND file lock is released
>
> #### Scenario: YAML parsing errors
> - WHEN config file contains invalid YAML
> - THEN YAMLError is raised with clear message
> - AND error includes file location

**Impact**:
- Users get cryptic error messages
- No validation of project names before operations
- File system errors not caught and wrapped
- YAML errors don't include helpful context
- Lock is released (good) but error context is lost

**Suggested Fix**:
```python
async def get_or_create_project_config(self, name: str) -> Project:
    """Get project config or create if it doesn't exist."""
    # Validate project name upfront
    import re
    if not name or not name.strip():
        raise ValueError("Project name cannot be empty")
    if not re.match(NAME_PATTERN, name):
        raise ValueError(
            f"Invalid project name '{name}': must contain only "
            "alphanumeric characters, underscores, and hyphens"
        )

    await self._ensure_initialized()

    async def _get_or_create(file_path: Path) -> Project:
        try:
            content = file_path.read_text()
        except OSError as e:
            raise IOError(f"Failed to read config file {file_path}: {e}") from e

        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(
                f"Invalid YAML in config file {file_path}: {e}"
            ) from e

        projects = data.get("projects", {})

        if name in projects:
            project_data = projects[name]
            try:
                return Project(**project_data)
            except Exception as e:
                raise ValueError(
                    f"Invalid project data for '{name}' in {file_path}: {e}"
                ) from e

        # Create new project
        project = Project(name=name)
        projects[name] = self._project_to_dict(project)
        data["projects"] = projects

        try:
            file_path.write_text(yaml.dump(data))
        except OSError as e:
            raise IOError(f"Failed to write config file {file_path}: {e}") from e

        return project

    return await lock_update(self.config_file, _get_or_create)
```

---

### 5. Re-implementation of Standard Library Functionality
**critical (dry, maintainability)**

**File**: `src/mcp_guide/file_lock.py:13-33`

**Location(s)**:
- `src/mcp_guide/file_lock.py:13-33` (_get_hostname function)

**Context**:
```python
def _get_hostname() -> str:
    """Get hostname in a cross-platform way."""
    try:
        # Try platform.node() first (works on Windows and Unix)
        hostname = platform.node()
        if hostname:
            return hostname.split(".")[0]
    except Exception:
        pass

    # Fallback to environment variables
    try:
        hostname_env = os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME")
        if hostname_env:
            return hostname_env.split(".")[0]
    except Exception:
        pass

    # Last resort
    return "unknown"
```

**Comments**:
This function re-implements `socket.gethostname()` from the standard library, which already handles cross-platform hostname detection correctly. The custom implementation adds unnecessary complexity and potential bugs.

**Impact**:
- Unnecessary code duplication
- `platform.node()` already calls `socket.gethostname()` internally
- The fallback logic is redundant
- Bare `except Exception` catches too much (violates best practices)

**Suggested Fix**:
```python
import socket

def _get_hostname() -> str:
    """Get hostname in a cross-platform way."""
    try:
        return socket.gethostname().split(".")[0]
    except OSError:
        return "unknown"
```

This is simpler, more reliable, and uses the standard library correctly.

---

## Warnings (8)

### 1. Inconsistent Async Context Manager Implementation
**warning (inconsistency)**

**File**: `src/mcp_guide/config.py:28-35`

**Location(s)**:
- `src/mcp_guide/config.py:28-35`

**Context**:
```python
async def __aenter__(self) -> "ConfigManager":
    """Async context manager entry."""
    await self._ensure_initialized()
    return self

async def __aexit__(self, *args: object) -> None:
    """Async context manager exit."""
    pass
```

**Issue**: The async context manager is implemented but does nothing useful. The `__aexit__` is empty, and initialization happens automatically anyway. This pattern suggests it was copied from somewhere but not adapted to this use case.

**Impact**: Misleading API - users might think they need to use `async with ConfigManager()` when they don't.

**Existing Pattern**: No other classes in the codebase use async context managers.

**Suggestion**: Either remove the context manager methods entirely, or document why they exist (perhaps for future resource management).

---

### 2. Mutable Default Argument in ContextVar
**warning (bug_risk)**

**File**: `src/mcp_guide/session.py:49`

**Location(s)**:
- `src/mcp_guide/session.py:49`

**Context**:
```python
active_sessions: ContextVar[dict[str, Session]] = ContextVar("active_sessions", default={})
```

**Issue**: Using a mutable default (`{}`) for ContextVar can lead to shared state issues. While ContextVar handles this correctly (each context gets its own copy), it's a common Python pitfall and could confuse readers.

**Impact**: Low - ContextVar implementation handles this correctly, but it's a code smell.

**Suggestion**:
```python
# More explicit - shows that each context gets a fresh dict
active_sessions: ContextVar[dict[str, Session]] = ContextVar("active_sessions")

def get_current_session(project_name: str) -> Optional[Session]:
    """Get current session for project from ContextVar."""
    sessions = active_sessions.get({})  # Default here instead
    return sessions.get(project_name)
```

---

### 3. Unnecessary Copy Operations in ContextVar Helpers
**warning (performance)**

**File**: `src/mcp_guide/session.py:57-69`

**Location(s)**:
- `src/mcp_guide/session.py:57-59` (set_current_session)
- `src/mcp_guide/session.py:62-65` (remove_current_session)

**Context**:
```python
def set_current_session(session: Session) -> None:
    """Set current session in ContextVar."""
    sessions = active_sessions.get().copy()  # Unnecessary copy
    sessions[session.project_name] = session
    active_sessions.set(sessions)


def remove_current_session(project_name: str) -> None:
    """Remove session from ContextVar."""
    sessions = active_sessions.get().copy()  # Unnecessary copy
    sessions.pop(project_name, None)
    active_sessions.set(sessions)
```

**Issue**: The `.copy()` calls are unnecessary. ContextVar already provides isolation between contexts. Copying adds overhead without benefit.

**Impact**: Minor performance overhead on every session operation.

**Suggestion**:
```python
def set_current_session(session: Session) -> None:
    """Set current session in ContextVar."""
    sessions = active_sessions.get({})
    sessions[session.project_name] = session
    active_sessions.set(sessions)


def remove_current_session(project_name: str) -> None:
    """Remove session from ContextVar."""
    sessions = active_sessions.get({})
    sessions.pop(project_name, None)
    active_sessions.set(sessions)
```

Actually, wait - the copy IS necessary because we're mutating the dict. Let me reconsider...

**Correction**: The copy is actually necessary to avoid mutating the dict in the parent context. This is correct. However, the pattern could be clearer:

```python
def set_current_session(session: Session) -> None:
    """Set current session in ContextVar."""
    # Copy to avoid mutating parent context's dict
    sessions = dict(active_sessions.get({}))
    sessions[session.project_name] = session
    active_sessions.set(sessions)
```

Using `dict()` constructor makes the intent clearer than `.copy()`.

---

### 4. Missing Length Validation in Models
**warning (data_integrity)**

**File**: `src/mcp_guide/models.py:51-68`

**Location(s)**:
- `src/mcp_guide/models.py:63-68` (validate_name)

**Context**:
```python
@field_validator("name")
@classmethod
def validate_name(cls, v: str) -> str:
    import re

    if not re.match(NAME_PATTERN, v):
        raise ValueError(f"Project name must contain only alphanumeric characters, underscores, and hyphens")
    return v
```

**Issue**: The spec specifies length constraints (1-50 chars for project, 1-30 for category/collection) but these are not validated.

**Spec Requirement**:
> ### Validation Rules
> - Project name: alphanumeric, hyphens, underscores, 1-50 chars
> - Category name: alphanumeric, hyphens, underscores, 1-30 chars
> - Collection name: alphanumeric, hyphens, underscores, 1-30 chars

**Impact**: Very long names could cause issues with file systems, UI display, or database storage.

**Suggestion**:
```python
@field_validator("name")
@classmethod
def validate_name(cls, v: str) -> str:
    import re

    if not v or len(v) > 50:
        raise ValueError("Project name must be between 1 and 50 characters")
    if not re.match(NAME_PATTERN, v):
        raise ValueError(
            "Project name must contain only alphanumeric characters, "
            "underscores, and hyphens"
        )
    return v
```

---

### 5. Regex Import Inside Validators
**warning (performance)**

**File**: `src/mcp_guide/models.py:24-28, 42-46, 63-68`

**Location(s)**:
- `src/mcp_guide/models.py:25` (Category.validate_name)
- `src/mcp_guide/models.py:43` (Collection.validate_name)
- `src/mcp_guide/models.py:64` (Project.validate_name)
- `src/mcp_guide/session.py:23` (Session.__post_init__)

**Context**:
```python
@field_validator("name")
@classmethod
def validate_name(cls, v: str) -> str:
    import re  # Imported on every validation call

    if not re.match(NAME_PATTERN, v):
        raise ValueError(...)
    return v
```

**Issue**: `import re` is called inside the validator, which means it's executed every time a model is created. While Python caches imports, this is still inefficient and unconventional.

**Impact**: Minor performance overhead, but more importantly it's a code smell.

**Suggestion**:
```python
import re  # At module level

NAME_PATTERN = r"^[a-zA-Z0-9_-]+$"
_NAME_REGEX = re.compile(NAME_PATTERN)  # Compile once

@pydantic_dataclass(frozen=True)
class Category:
    """Category configuration."""

    name: str
    dir: str
    patterns: list[str]

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not _NAME_REGEX.match(v):
            raise ValueError(...)
        return v
```

---

### 6. Incomplete Test Coverage for Edge Cases
**warning (test_coverage)**

**File**: `tests/test_config.py`, `tests/test_session.py`, `tests/test_models.py`

**Issue**: While coverage is good (87% overall), several edge cases are not tested:

**Missing Test Cases**:

1. **ConfigManager with corrupted YAML**:
   - What happens if config file contains invalid YAML?
   - Spec requires YAMLError with file location

2. **ConfigManager with permission errors**:
   - What happens if config file is not readable/writable?
   - Spec requires IOError with clear message

3. **Session with invalid project name characters**:
   - Test exists for empty name, but not for invalid characters
   - Should test names like "project@name", "project name", "project/name"

4. **Project model with very long names**:
   - No tests for length limits (spec says 1-50 chars)

5. **Category with empty patterns list**:
   - Spec requires non-empty validation, but no test verifies this

6. **File lock with permission denied**:
   - What happens if lock file cannot be created?

**Impact**: Edge cases may cause unexpected failures in production.

**Suggestion**: Add tests for these scenarios before considering the implementation complete.

---

### 7. Inconsistent Error Messages
**warning (usability)**

**File**: `src/mcp_guide/config.py:98-108, 112-122`

**Location(s)**:
- `src/mcp_guide/config.py:98` (rename_project)
- `src/mcp_guide/config.py:116` (delete_project)

**Context**:
```python
if old_name not in projects:
    raise ValueError(f"Project '{old_name}' not found")
if new_name in projects:
    raise ValueError(f"Project '{new_name}' already exists")
```

**Issue**: Error messages use different formats:
- `"Project '{name}' not found"` (rename, delete)
- No error message for invalid names (not validated)
- No error message for YAML errors (not caught)

**Impact**: Inconsistent user experience, harder to parse errors programmatically.

**Suggestion**: Standardize error messages:
```python
# Use consistent format
raise ValueError(f"Project not found: {old_name}")
raise ValueError(f"Project already exists: {new_name}")
raise ValueError(f"Invalid project name: {name}")
```

---

### 8. Missing Docstring Details
**warning (documentation)**

**File**: `src/mcp_guide/config.py`, `src/mcp_guide/session.py`, `src/mcp_guide/models.py`

**Issue**: While all public methods have docstrings, they lack important details:

1. **ConfigManager methods** don't document:
   - What exceptions can be raised
   - Thread safety guarantees
   - Whether operations are atomic

2. **Session methods** don't document:
   - That get_project() caches the result
   - That update_config() invalidates the cache
   - Concurrency behavior with ContextVar

3. **Model methods** don't document:
   - Validation rules for each field
   - What makes a valid name/pattern/directory

**Impact**: Developers need to read the code to understand behavior.

**Suggestion**: Enhance docstrings with examples and details:
```python
async def get_or_create_project_config(self, name: str) -> Project:
    """Get project config or create if it doesn't exist.

    Args:
        name: Project name (alphanumeric, hyphens, underscores only)

    Returns:
        Project configuration

    Raises:
        ValueError: If project name is invalid
        IOError: If config file cannot be read/written
        yaml.YAMLError: If config file contains invalid YAML

    Note:
        This operation is atomic and thread-safe due to file locking.
        If the project doesn't exist, a new one is created with default settings.
    """
```

---

## Notes (3)

### 1. Alternative Singleton Pattern
**Note**: Different approach than typical Python singletons

**File**: `src/mcp_guide/config.py:20-26`

**Note**: The implementation uses `__new__` for singleton pattern, which is one approach. However, Python has several singleton patterns:

1. **Module-level instance** (simplest):
   ```python
   # config.py
   _config_manager = ConfigManager()

   def get_config_manager() -> ConfigManager:
       return _config_manager
   ```

2. **Metaclass** (most Pythonic):
   ```python
   class SingletonMeta(type):
       _instances = {}
       def __call__(cls, *args, **kwargs):
           if cls not in cls._instances:
               cls._instances[cls] = super().__call__(*args, **kwargs)
           return cls._instances[cls]

   class ConfigManager(metaclass=SingletonMeta):
       ...
   ```

3. **Decorator** (explicit):
   ```python
   def singleton(cls):
       instances = {}
       def get_instance(*args, **kwargs):
           if cls not in instances:
               instances[cls] = cls(*args, **kwargs)
           return instances[cls]
       return get_instance

   @singleton
   class ConfigManager:
       ...
   ```

**Not a Problem**: The current approach works, but consider alternatives if the constructor injection issue needs to be solved.

---

### 2. YAML vs JSON for Config Format
**Note**: Different format than typical Python projects

**File**: `src/mcp_guide/config.py:9, 45, 59, 77, 90, 105, 119`

**Note**: The implementation uses YAML for configuration, while the original `config_paths.py` referenced `config.json`. YAML is more human-readable but:

**Pros**:
- More readable for humans
- Supports comments
- Better for configuration files

**Cons**:
- Slower to parse than JSON
- More complex parser (security considerations)
- Spec says `config.yaml` but `config_paths.py` still references `.json`

**Inconsistency**: `src/mcp_guide/config_paths.py:61` still has old comment:
```python
def get_default_config_file() -> Path:
    """Get default configuration file path (backward compatibility)."""
    return get_config_file()
```

The function returns `.yaml` but the old code expected `.json`. This could cause migration issues.

**Suggestion**: Add migration logic or document the breaking change.

---

### 3. Test Isolation Strategy is Fragile
**Note**: Tests rely on environment variable manipulation

**File**: `tests/conftest.py:11-35`

**Note**: The test isolation strategy relies on `pytest_configure` hook to override environment variables BEFORE any imports. This works but is fragile:

**Issues**:
1. Timing-dependent (must run before imports)
2. Global state modification
3. Doesn't work for per-test isolation
4. ConfigManager ignores `isolated_config_file` fixture

**Better Approach**: Constructor injection (see Critical Issue #1) would allow:
```python
@pytest.fixture
def isolated_config_manager(tmp_path):
    """Provide ConfigManager with isolated config directory."""
    return ConfigManager(config_dir=str(tmp_path))
```

This is more explicit, more reliable, and easier to understand.

---

## Summary of Required Actions

### Before Approval (Critical)
1. ✅ **Add constructor injection** to ConfigManager for test isolation
2. ✅ **Fix singleton thread safety** with proper double-checked locking
3. ✅ **Add missing validation** for patterns, directory, and collection categories
4. ✅ **Implement error handling** for YAML parsing, file system errors, and invalid names
5. ✅ **Replace custom hostname function** with `socket.gethostname()`

### Recommended (Warnings)
6. ⚠️ **Add length validation** to model names (1-50 chars for project, 1-30 for category/collection)
7. ⚠️ **Move regex import** to module level and compile once
8. ⚠️ **Add edge case tests** for corrupted YAML, permission errors, invalid characters
9. ⚠️ **Standardize error messages** across all operations
10. ⚠️ **Enhance docstrings** with exceptions, examples, and behavior details

### Optional (Notes)
11. 📝 Consider removing async context manager if not needed
12. 📝 Document YAML vs JSON migration path
13. 📝 Consider alternative singleton patterns for better testability

## Test Results

✅ All 57 tests pass
✅ Type checking clean (mypy)
✅ Linting clean (ruff)
✅ 87% overall coverage (95%+ for critical modules)

However, tests pass due to environment variable manipulation rather than proper constructor injection, making the test suite fragile.

## Conclusion

The implementation delivers the core functionality successfully, but has **5 critical issues** that must be fixed before production use. The most important is the missing constructor injection for testing, which makes the current test suite fragile and violates the specification. The singleton pattern also has a race condition that could cause bugs under concurrent access.

Once these critical issues are addressed, this will be a solid foundation for the config and session management system.
