# Tasks: Remove Old Rendering Code

## Analysis
- [x] Identify unused rendering functions
- [x] Verify no remaining usages in codebase
- [x] Identify associated tests to remove

## Code Removal
- [x] Remove `src/mcp_guide/utils/system_content.py` (entire file)
- [x] Remove `render_file_content()` from `src/mcp_guide/utils/template_renderer.py`
- [x] Remove `tests/unit/test_system_content.py` (entire file)
- [x] Remove `render_file_content` tests from `tests/test_template_renderer.py`
- [x] Remove unused import from `template_renderer.py`

## Verification
- [x] Run all tests to ensure nothing breaks (1293 passed)
- [x] Run mypy to ensure no type errors (127 files clean)
- [x] Search for any remaining references (none found)

## Notes
- `render_workflow_template()`, `render_openspec_template()`, and `render_context_template()` are thin wrappers still in use - kept them
- `render_file_content()` was only used by `render_system_content()` - both removed
- All dead code successfully removed after migrations complete
