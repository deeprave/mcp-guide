## 1. Architecture Refactoring

- [ ] 1.1 Move ConfigManager class inside Session as `_ConfigManager` (private inner class)
- [ ] 1.2 Make ConfigManager a class-level singleton with reconfiguration capability
- [ ] 1.3 Add ConfigManager.reconfigure() method for changing config directory
- [ ] 1.4 Update Session constructor signature: `Session(project_name: str, *, _config_dir_for_tests: Optional[str] = None)`
- [ ] 1.5 Add Session instance variable for current project key (with hash suffix)
- [ ] 1.6 Add async locking for ConfigManager singleton access

## 2. ConfigManager Improvements

- [ ] 2.1 Implement ConfigManager.reconfigure() method with proper locking
- [ ] 2.2 Separate legacy project migration into dedicated function
- [ ] 2.3 Update project loading to return (project_key, project_data) tuple
- [ ] 2.4 Update project saving to accept (project_key, project_data) parameters
- [ ] 2.5 Optimize non-legacy project loading to avoid unnecessary work

## 3. Session Function Updates

- [ ] 3.1 Update `get_or_create_session()` to use `*, _config_dir_for_tests: Optional[str] = None`
- [ ] 3.2 Remove temporary ConfigManager creation from `resolve_project_by_name()`
- [ ] 3.3 Update `resolve_project_name_to_key()` to use Session's singleton ConfigManager
- [ ] 3.4 Update `get_project_info()` to use Session's ConfigManager instead of creating new instance
- [ ] 3.5 Ensure all test-related parameters are keyword-only with underscore prefix

## 3. Integration Test Updates

- [ ] 3.1 Update `tests/integration/test_config_session.py` to use keyword-only `_config_dir_for_tests`
- [ ] 3.2 Update `tests/integration/test_project_resolution.py` to use Session-based approach
- [ ] 3.3 Update `tests/integration/test_config_docroot.py` to use Session instead of direct ConfigManager
- [ ] 3.4 Update `tests/integration/test_feature_flag_tools.py` to use Session-based approach
- [ ] 3.5 Update `tests/integration/test_tool_registration.py` to use Session-based approach

## 4. Unit Test Updates

- [ ] 4.1 Update `tests/test_config.py` to test ConfigManager through Session interface
- [ ] 4.2 Update `tests/test_session.py` to use new Session constructor pattern
- [ ] 4.3 Update `tests/unit/test_config_*.py` files to access ConfigManager through Session
- [ ] 4.4 Update tool unit tests that create ConfigManager instances directly

## 5. Tool Integration Updates

- [ ] 5.1 Update tool tests in `tests/unit/test_mcp_guide/tools/` that create ConfigManager instances
- [ ] 5.2 Ensure all tool code accesses ConfigManager through Session interface
- [ ] 5.3 Update any remaining direct ConfigManager usage in tool implementations

## 6. Legacy Migration Improvements

- [ ] 6.1 Create dedicated `_migrate_legacy_project()` function
- [ ] 6.2 Optimize project loading to detect legacy format early
- [ ] 6.3 Ensure migration only runs once per legacy project
- [ ] 6.4 Update project key tracking in Session instances

## 6. Validation and Testing

- [ ] 6.1 Run all unit tests to ensure no regressions
- [ ] 6.2 Run all integration tests to verify new patterns work correctly
- [ ] 6.3 Test session isolation in concurrent scenarios
- [ ] 6.4 Verify config file operations still work correctly
- [ ] 6.5 Test error handling for invalid config directories
- [ ] 6.6 Verify ConfigManager singleton behavior under concurrent access
- [ ] 6.7 Test legacy project migration only runs once

## 7. Documentation Updates

- [ ] 7.1 Update ConfigManager class docstring to reflect singleton status
- [ ] 7.2 Update Session class docstring to document ConfigManager encapsulation and project key tracking
- [ ] 7.3 Document keyword-only test parameter conventions
- [ ] 7.4 Update any developer documentation that references ConfigManager usage patterns
