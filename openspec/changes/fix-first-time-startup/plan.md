# Implementation Plan: fix-first-time-startup

## Overview
Fix `lock_update()` in `file_lock.py` to handle missing parent directory during first-time startup.

## Changes Required

### 1. Create custom exception in `src/mcp_guide/file_lock.py`

**Add at top of file:**
```python
class ConfigDirectoryError(Exception):
    """Fatal error: cannot create or access config directory."""
    pass
```

### 2. Modify `src/mcp_guide/file_lock.py`

**Location:** Line 68 in the `lock_update()` function where lock file creation happens

**Current code:**
```python
while True:
    # Attempt to create the lock file
    try:
        with open(lock_file, "x") as lockfile:
            lockfile.write(f"{hostname}:{pid}")
        break
    except FileExistsError:
        # ... existing logic ...
```

**New code:**
```python
while True:
    # Attempt to create the lock file
    try:
        with open(lock_file, "x") as lockfile:
            lockfile.write(f"{hostname}:{pid}")
        break
    except FileNotFoundError:
        # Parent directory doesn't exist - try to create it
        if not lock_file.parent.exists():
            try:
                lock_file.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                logger.exception(f"Failed to create config directory: {lock_file.parent}")
                raise ConfigDirectoryError(f"Cannot create config directory: {lock_file.parent}")
        
        # Retry lock creation
        try:
            with open(lock_file, "x") as lockfile:
                lockfile.write(f"{hostname}:{pid}")
            break
        except Exception:
            logger.exception(f"Failed to create lock file after creating parent: {lock_file}")
            raise ConfigDirectoryError(f"Cannot create lock file: {lock_file}")
    except FileExistsError:
        # ... existing logic ...
```

**Import needed:** Add `logger` import at top of file

### 3. Modify main entry point to catch ConfigDirectoryError

**File:** Find main entry point (likely `src/mcp_guide/server.py` or `src/mcp_guide/__main__.py`)

**Add exception handler:**
```python
try:
    # existing main logic
except ConfigDirectoryError as e:
    logger.error(f"Fatal: {e}")
    sys.exit(2)  # Exit code 2: cannot meet conditions to run MCP
```

### 4. Add Tests

**File:** `tests/test_file_lock.py`

Add test cases:
- `test_lock_update_creates_parent_directory` - Success case
- `test_lock_update_raises_on_parent_creation_failure` - Parent creation fails, raises ConfigDirectoryError
- `test_lock_update_raises_on_lock_creation_after_parent` - Lock creation fails after parent created, raises ConfigDirectoryError

## Implementation Steps

1. Add `ConfigDirectoryError` exception class to `file_lock.py`
2. Add logger import to `file_lock.py`
3. Wrap lock creation in FileNotFoundError handler
4. Check parent directory existence
5. Create parent with error handling and raise ConfigDirectoryError
6. Retry lock creation with error handling and raise ConfigDirectoryError
7. Find main entry point and add exception handler for ConfigDirectoryError with exit code 2
8. Add unit tests for all scenarios
9. Test end-to-end first-time startup

## Success Criteria

- First-time startup with non-existent `~/.config/mcp-guide` succeeds
- Config directory is created automatically
- Templates are installed
- Fatal errors log full stack trace and raise ConfigDirectoryError
- Main catches ConfigDirectoryError and exits with code 2
- All tests pass
