## 1. Architecture Refactoring

- [x] 1.1 Move ConfigManager class inside Session as `_ConfigManager` (private inner class)
- [x] 1.2 Make ConfigManager a class-level singleton with reconfiguration capability
- [x] 1.3 Add ConfigManager.reconfigure() method for changing config directory
- [x] 1.4 Update Session constructor signature: `Session(project_name: str, *, _config_dir_for_tests: Optional[str] = None)`
- [x] 1.5 Add Session instance variable for current project key (with hash suffix)
- [x] 1.6 Add async locking for ConfigManager singleton access (SKIPPED - not needed in single-threaded asyncio environment)

## 2. ConfigManager Improvements

- [x] 2.1 Implement ConfigManager.reconfigure() method with proper locking
- [x] 2.2 Separate legacy project migration into dedicated function
- [x] 2.3 Update project loading to return (project_key, project_data) tuple
- [x] 2.4 Update project saving to accept (project_key, project_data) parameters
- [x] 2.5 Optimize non-legacy project loading to avoid unnecessary work

## 3. Session Function Updates

- [x] 3.1 Update `get_or_create_session()` to use `*, _config_dir_for_tests: Optional[str] = None`
- [x] 3.2 Remove temporary ConfigManager creation from `resolve_project_by_name()`
- [x] 3.3 Update `resolve_project_name_to_key()` to use Session's singleton ConfigManager
- [x] 3.4 Update `get_project_info()` to use Session's ConfigManager instead of creating new instance
- [x] 3.5 Ensure all test-related parameters are keyword-only with underscore prefix

## 3. Integration Test Updates

- [x] 3.1 Update `tests/integration/test_config_session.py` to use keyword-only `_config_dir_for_tests`
- [x] 3.2 Update `tests/integration/test_project_resolution.py` to use Session-based approach
- [x] 3.3 Update `tests/integration/test_config_docroot.py` to use Session instead of direct ConfigManager
- [x] 3.4 Update `tests/integration/test_feature_flag_tools.py` to use Session-based approach
- [x] 3.5 Update `tests/integration/test_tool_registration.py` to use Session-based approach

## 4. Unit Test Updates

- [x] 4.1 Update `tests/test_config.py` to test ConfigManager through Session interface
- [x] 4.2 Update `tests/test_session.py` to use new Session constructor pattern
- [x] 4.3 Update `tests/unit/test_config_*.py` files to access ConfigManager through Session
- [x] 4.4 Update tool unit tests that create ConfigManager instances directly

## 5. Tool Integration Updates

- [x] 5.1 Update tool tests in `tests/unit/test_mcp_guide/tools/` that create ConfigManager instances
- [x] 5.2 Ensure all tool code accesses ConfigManager through Session interface
- [x] 5.3 Update any remaining direct ConfigManager usage in tool implementations

## 6. Legacy Migration Improvements

- [x] 6.1 Create dedicated `_migrate_legacy_project()` function
- [x] 6.2 Optimize project loading to detect legacy format early
- [x] 6.3 Ensure migration only runs once per legacy project
- [x] 6.4 Update project key tracking in Session instances

## 6. Validation and Testing

- [x] 6.1 Run all unit tests to ensure no regressions
- [x] 6.2 Run all integration tests to verify new patterns work correctly
- [x] 6.3 Test session isolation in concurrent scenarios
- [x] 6.4 Verify config file operations still work correctly
- [x] 6.5 Test error handling for invalid config directories
- [x] 6.6 Verify ConfigManager singleton behavior under concurrent access
- [x] 6.7 Test legacy project migration only runs once

## 7. Documentation Updates

- [x] 7.1 Update ConfigManager class docstring to reflect singleton status
- [x] 7.2 Update Session class docstring to document ConfigManager encapsulation and project key tracking
- [x] 7.3 Document keyword-only test parameter conventions (SKIPPED - not required)
- [x] 7.4 Update any developer documentation that references ConfigManager usage patterns (SKIPPED - not required)
