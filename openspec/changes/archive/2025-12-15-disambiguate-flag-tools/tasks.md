# Implementation Tasks: Disambiguate Feature Flag Tools

## Implementation Phase

### Pre-Check
- [x] Run complete test suite to ensure all tests pass before changes
  - Establish baseline - all tests must pass before starting implementation

### Rename Existing Tools (Project Flags)
- [x] Rename `set_flag` function to `set_project_flag` in tool_feature_flags.py
  - Update function name, docstring, and @tools.tool decorator registration
- [x] Rename `get_flag` function to `get_project_flag` in tool_feature_flags.py
  - Update function name, docstring, and @tools.tool decorator registration
- [x] Rename `list_flags` function to `list_project_flags` in tool_feature_flags.py
  - Update function name, docstring, and @tools.tool decorator registration

### Create New Global Flag Tools
- [x] Create `SetFeatureFlagArgs` class for global flag operations
  - Similar to SetFlagArgs but for global flags
- [x] Create `GetFeatureFlagArgs` class for global flag operations
  - Similar to GetFlagArgs but for global flags
- [x] Create `ListFeatureFlagsArgs` class for global flag operations
  - Similar to ListFlagsArgs but for global flags
- [x] Implement `set_feature_flag` function for global flags
  - Uses session.feature_flags() instead of session.project_flags()
- [x] Implement `get_feature_flag` function for global flags
  - Uses session.feature_flags() only, no resolution hierarchy
- [x] Implement `list_feature_flags` function for global flags
  - Uses session.feature_flags() only, no merging with project flags

### Update Tests
- [x] Update any existing tests to use new function names
  - Find and update test files that reference the old function names

### Code Quality Improvements
- [x] Fix GetFlagArgs docstring to reference correct tool name
- [x] Extract duplicate validation logic into helper function

## Check Phase
- [x] Run complete test suite to verify all changes work correctly
  - Ensure 100% test pass rate with no regressions
- [x] Verify all renamed tools work with existing behavior
- [x] Verify new global flag tools work correctly
- [x] Test flag resolution hierarchy still works as expected
