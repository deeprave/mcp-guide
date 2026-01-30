# Change: Migrate Workflow Rendering to render_template() API

**Status**: Proposed
**Priority**: High
**Complexity**: Low
**Parent**: unify-template-rendering

## Why

Workflow templates currently use `render_system_content()` which internally calls the legacy `render_file_content()` API. This is the last major rendering path that hasn't been migrated to the unified `render_template()` API.

Without migration:
- Inconsistent rendering behavior across the codebase
- Cannot benefit from improved error handling in render_template()
- Partial resolution bugs may exist (like the command rendering bug we just fixed)
- Maintenance burden of supporting two rendering paths

## What Changes

- Update `render_system_content()` in `utils/system_content.py` to use `render_template()` API
- Replace Result-based error handling with exception-based handling
- Use template's parent directory for base_dir (fixes potential partial resolution issues)
- Add specific exception handling (FileNotFoundError, PermissionError, RuntimeError)

## Impact

- Affected specs: workflow-system
- Affected code:
  - `src/mcp_guide/utils/system_content.py` - Core migration
  - Tests for system content rendering
- No changes needed to:
  - `src/mcp_guide/workflow/rendering.py` - Wrappers unchanged
  - `src/mcp_guide/workflow/tasks.py` - Consumers unchanged
  - `src/mcp_guide/client_context/openspec_task.py` - Consumers unchanged

## Technical Approach

Similar to command rendering migration but simpler:
- No argument validation needed (system templates don't have user arguments)
- No requires-* checking needed (system templates always render)
- Maintain Result[str] return type for backward compatibility
- Handle exceptions internally and convert to Result

## Success Criteria

1. render_system_content() uses render_template() API
2. All workflow templates render correctly
3. Common templates with extra context work
4. Partial resolution works for system templates
5. All tests pass
6. No regressions in workflow functionality
