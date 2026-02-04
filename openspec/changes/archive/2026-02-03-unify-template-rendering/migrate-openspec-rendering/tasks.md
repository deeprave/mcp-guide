# Implementation Tasks: Migrate OpenSpec Rendering

## 1. Preparation
- [x] Create subspec structure
- [x] Review all OpenSpec template usage
- [x] Identify all partial references to update

## 2. Move Templates
- [x] Move 4 templates from _common/ to _openspec/
- [x] Move 4 format partials from _commands/openspec/ to _openspec/

## 3. Update Partial References
- [x] Find all templates referencing moved partials
- [x] Update partial paths to _openspec/ directory

## 4. Create render_openspec_template() (TDD)
- [x] Create openspec_content.py module
- [x] Create openspec_rendering.py wrapper
- [x] Add extra_context support

## 5. Update Callers
- [x] Update openspec_task.py to use new function
- [x] Update test mocks
- [x] Handle None returns from rendering

## 6. Testing
- [x] Test all OpenSpec template rendering
- [x] Run full test suite (1300 tests passing)

## 7. Evaluate Commonality
- [x] Compare with render_workflow_template()
- [x] Decide if common helper is warranted
- [x] Created unified render_content() function
- [x] Both workflow and openspec now use render_content()
- [x] Added extensibility via discover_files and process_context callbacks

## 8. Return RenderedContent
- [x] Changed render_content() to return RenderedContent | None
- [x] Updated render_workflow_template() to return RenderedContent | None
- [x] Updated render_openspec_template() to return RenderedContent | None
- [x] Preserved instruction metadata throughout rendering pipeline
- [x] Updated all test mocks to use RenderedContent objects

## 9. Centralize Constants
- [x] Moved WORKFLOW_DIR to config_constants.py
- [x] Moved OPENSPEC_DIR to config_constants.py
- [x] Centralized with COMMANDS_DIR

## 10. Add Development Flag
- [x] Created add-development-feature-flag subspec
- [x] Added FLAG_GUIDE_DEVELOPMENT constant
- [x] Added validate_boolean_flag() validator
- [x] Updated discover_commands() to skip mtime checks in production

## 11. Validation
- [x] All tests pass without warnings (1293 passing)
- [x] Ruff check passes
- [x] Mypy passes
- [x] Manual test of OpenSpec commands
