# Change: Remove Old Template Rendering Functions

## Why
After all migrations complete, old rendering functions are no longer used. Clean up to prevent confusion and maintain single rendering path.

## What Changes
- Remove `render_system_content()` from `utils/system_content.py`
- Remove `render_workflow_template()` wrapper
- Remove `render_common_template()` wrapper
- Update any remaining references

## Impact
- Affected specs: template-system
- Affected code:
  - `src/mcp_guide/utils/system_content.py`
  - `src/mcp_guide/workflow/rendering.py`
