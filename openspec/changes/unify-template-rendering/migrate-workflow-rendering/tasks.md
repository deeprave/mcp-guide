# Implementation Tasks: Migrate Workflow Rendering

## 1. Preparation
- [x] Review render_system_content() implementation
- [x] Identify all callers of workflow rendering functions
- [x] Review lessons learned from command rendering migration

## 2. Core Migration (TDD)
- [x] RED: Add test for render_system_content with render_template API
- [x] GREEN: Update render_system_content to use render_template()
- [x] REFACTOR: Update imports and error handling
- [x] Use template's parent directory for base_dir (partial resolution fix)

## 3. Exception Handling
- [x] Replace Result-based errors with exceptions
- [x] Add specific exception handling (FileNotFoundError, PermissionError, RuntimeError)
- [x] Add appropriate logging with logger.debug()

## 4. Testing
- [x] Test workflow template rendering
- [x] Test error scenarios (missing file, permission denied, syntax error)
- [x] Test partial resolution in system templates
- [x] Run full test suite

## 5. Validation
- [x] All tests pass without warnings
- [x] Ruff check passes
- [x] Mypy passes
- [ ] Manual test of workflow phase transitions
- [ ] Manual test of monitoring templates
