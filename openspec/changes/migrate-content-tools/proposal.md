# Change: Migrate Content Tools to New Renderer

## Why
Content retrieval tools (`get_content`, category content) currently use fragmented template rendering. Need to migrate to new `render_template()` function for consistency.

## What Changes
- Update `read_and_render_file_contents()` to use `render_template()`
- Update content tools to handle `RenderedContent` objects
- Remove old rendering path from content utilities

## Impact
- Affected specs: content-retrieval
- Affected code:
  - `src/mcp_guide/utils/content_utils.py`
  - `src/mcp_guide/tools/tool_content.py`
  - `src/mcp_guide/tools/tool_category.py`
