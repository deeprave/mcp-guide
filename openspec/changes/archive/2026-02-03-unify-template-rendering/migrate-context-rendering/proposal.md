# Change: Migrate Common Template Rendering to New Renderer

## Why
Common templates currently use `render_common_template()` wrapper. Need to migrate to new `render_template()` function for consistency.

## What Changes
- Update `workflow/rendering.py` to use `render_template()` for common templates
- Update OpenSpec and other tasks using common templates
- Remove `render_common_template()` wrapper

## Impact
- Affected specs: template-system
- Affected code:
  - `src/mcp_guide/workflow/rendering.py`
  - `src/mcp_guide/client_context/openspec_task.py`
  - `src/mcp_guide/client_context/tasks.py`
