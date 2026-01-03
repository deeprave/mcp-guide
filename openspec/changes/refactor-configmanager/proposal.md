# Change: Refactor ConfigManager to be Private to Session

## Why

ConfigManager is currently a standalone class that can be instantiated and injected into Session, violating encapsulation principles. This creates several problems:

1. **Encapsulation violation**: ConfigManager can be created anywhere, making it difficult to ensure proper lifecycle management
2. **Test brittleness**: Integration tests directly create and inject ConfigManager instances, making them fragile and harder to maintain
3. **Architectural confusion**: The dependency injection pattern suggests ConfigManager might be shared, but it's actually meant to be owned by Session
4. **Potential for misuse**: Multiple ConfigManager instances could theoretically exist, leading to inconsistent state

## What Changes

- **BREAKING**: ConfigManager becomes a private inner class of Session (`Session._ConfigManager`)
- **BREAKING**: Session constructor signature changes from `Session(_config_manager: ConfigManager, project_name: str)` to `Session(project_name: str, *, _config_dir_for_tests: Optional[str] = None)`
- **BREAKING**: ConfigManager becomes a class-level singleton within Session that can be reconfigured
- Session maintains single ConfigManager instance that can be reconfigured for different config directories
- `get_or_create_session()` and related functions use keyword-only `_config_dir_for_tests` parameters
- Session tracks current project key (with hash suffix) separately from Project data
- All tests updated to use new Session constructor pattern
- ConfigManager can no longer be instantiated directly outside of Session

## Impact

- **Affected specs**: session-management
- **Affected code**:
  - `src/mcp_guide/session.py` - Session class and related functions
  - `src/mcp_guide/config.py` - ConfigManager class (moved inside Session)
  - All integration tests that create ConfigManager instances
  - Unit tests for Session and ConfigManager
- **Breaking changes**: Any code that directly creates ConfigManager instances will need to be updated
- **Test impact**: All integration tests need to be updated to use new Session constructor pattern
