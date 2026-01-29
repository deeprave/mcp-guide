# Change: Migrate Workflow Rendering to New Renderer

## Why
Workflow templates currently use `render_workflow_template()` wrapper. Need to migrate to new `render_template()` function for consistency.

## What Changes
- Update `workflow/rendering.py` to use `render_template()`
- Update workflow tasks to handle `RenderedContent` objects
- Remove `render_workflow_template()` wrapper

## Impact
- Affected specs: workflow-system
- Affected code:
  - `src/mcp_guide/workflow/rendering.py`
  - `src/mcp_guide/workflow/tasks.py`
