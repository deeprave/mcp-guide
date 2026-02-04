# Change: Migrate OpenSpec Rendering to render_template() API

**Status**: Proposed
**Priority**: High
**Complexity**: Medium
**Parent**: unify-template-rendering

## Why

OpenSpec templates are currently scattered across `_common/` and `_commands/openspec/` directories and rendered using `render_common_template()`. This is inconsistent with the unified template rendering approach and makes OpenSpec template organization unclear.

Without migration:
- OpenSpec templates not properly organized in dedicated directory
- Inconsistent rendering behavior with workflow templates
- Cannot benefit from improved error handling in render_template()
- Maintenance burden of supporting multiple rendering paths

## What Changes

- Move all OpenSpec templates to `_openspec/` directory (8 templates total)
- Create `render_openspec_template()` function following workflow pattern
- Update `openspec_task.py` to use new rendering function
- Update partial references in templates to point to new locations
- Evaluate similarity with workflow rendering for potential consolidation

## Impact

- Affected code:
  - `src/mcp_guide/client_context/openspec_task.py` - Use new function
  - `src/mcp_guide/templates/_openspec/` - Consolidated template location
  - Templates referencing OpenSpec partials - Updated paths
- No breaking changes to OpenSpec functionality
- Clearer template organization

## Technical Approach

Similar to workflow rendering migration:
- Create dedicated rendering module
- Use render_template() API with proper base_dir
- Centralized exception handling
- Return `str | None` for filtered templates

After implementation, evaluate if `render_workflow_template()` and `render_openspec_template()` are similar enough to warrant a generic `render_template_common()` helper.

## Success Criteria

1. All OpenSpec templates in `_openspec/` directory
2. render_openspec_template() uses render_template() API
3. All partial references updated and working
4. All tests pass
5. No regressions in OpenSpec functionality
6. Decision made on common helper (with rationale)
