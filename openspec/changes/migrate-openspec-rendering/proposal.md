# Change: Migrate OpenSpec Template Rendering to New Renderer

## Why
OpenSpec templates currently use common template rendering. Need dedicated integration with new `render_template()` function.

## What Changes
- Update `openspec_task.py` to use `render_template()` directly
- Handle `RenderedContent` objects in OpenSpec task
- Create helper for converting `RenderedContent` to task instructions

## Impact
- Affected specs: openspec-integration
- Affected code:
  - `src/mcp_guide/client_context/openspec_task.py`
