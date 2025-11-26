# Test File Protection

**Status**: Proposed
**Phase**: 3 - Testing Infrastructure
**Priority**: High
**Complexity**: Low
**Estimated Effort**: ~1 hour

## Problem Statement

Integration tests that exercise ProjectConfigManager and document operations risk corrupting production files if tests fail to properly isolate their operations. A single bug in test setup (e.g., using production paths instead of temporary directories) could silently overwrite user configuration or documents, causing data loss.

### Importance

- **Data Integrity**: Production config and documents are critical user data that must never be modified during testing
- **Test Reliability**: Silent corruption makes debugging extremely difficult - tests may pass while destroying production data
- **Developer Safety**: Prevents accidental data loss during test development and execution
- **CI/CD Safety**: Ensures automated test runs cannot corrupt production environments

## Protected Paths

The following paths require monitoring during test execution:

1. **Production Config File**: `~/.config/mcp-guide/config.json`
   - **Reason**: Contains all project configurations, categories, collections
   - **Impact**: Loss would destroy all user project setups

2. **Production Document Tree** (docroot): `~/.local/share/mcp-guide/`
   - **Monitoring**: Recursive (`recursive=True`) - all subdirectories and files
   - **Includes**: Category directories, `__docs__/` folders, document files, metadata
   - **Reason**: Contains all user-created and managed documentation
   - **Impact**: Loss would destroy all indexed documentation and metadata

## Possible Solutions

### 1. End-of-Session Hash Checking
Calculate hashes of protected files before tests, verify unchanged after completion.
- **Pros**: Simple, no dependencies
- **Cons**: Only detects corruption after damage is done, no immediate feedback

### 2. Environment Variable Guards
Check environment variable in production code to prevent operations during tests.
- **Pros**: Simple implementation
- **Cons**: Pollutes production code with test-specific logic, code smell

### 3. Filesystem Monitoring (watchdog)
Monitor protected paths during test execution, immediately terminate on modification.
- **Pros**: Immediate feedback, clean production code, comprehensive protection
- **Cons**: Additional dependency, slightly more complex setup

### 4. Mock/Patch All File Operations
Mock all filesystem operations in tests to prevent real file access.
- **Pros**: Complete isolation
- **Cons**: Doesn't test real file operations, defeats purpose of integration tests

## Chosen Solution: Watchdog Monitoring

**Rationale**:
- **Immediate Detection**: Test terminates instantly when production file is touched
- **Clean Architecture**: No test-specific code in production modules
- **Comprehensive**: Monitors both files and directories recursively
- **Developer Experience**: Clear error message shows exactly which file was modified
- **Minimal Overhead**: Only active during test execution

## Technical Approach

### Watchdog Configuration
```python
from mcp_guide.config_paths import get_default_config_file, get_default_docroot

# Monitor production config file directory
config_path = get_default_config_file().parent
observer.schedule(handler, str(config_path), recursive=False)

# Monitor production document tree (recursive)
docroot_path = get_default_docroot()
observer.schedule(handler, str(docroot_path), recursive=True)
```

### Path Resolution
Paths use XDG Base Directory specification (Unix) and APPDATA (Windows):
- **Config**: `$XDG_CONFIG_HOME/mcp-guide/` or `~/.config/mcp-guide/` (fallback)
- **Docroot**: `{config_dir}/docs/` (relative to config directory)

### Event Handler Behavior
- **Trigger on**: `modified`, `created`, `deleted`, `moved` events
- **Action**: `pytest.exit("Production file modified: {path}", returncode=1)`
- **Ignore**: Temporary files, lock files (if needed)

## Dependencies

- `watchdog` package (Python filesystem monitoring library) - add to dev dependencies

## Success Criteria

- Watchdog installed as dev dependency
- Fixture monitors both protected paths
- Tests terminate immediately on production file modification
- Normal test execution unaffected
- Clear error messages identify modified files

## Estimated Scope

- **Path helpers**: ~20 lines (config_paths.py module)
- **Fixture**: ~30 lines (conftest.py with handler)
- **Tests**: ~20 lines (validation tests)
- **Total**: ~70 LOC
- **Time**: ~1.5 hours
