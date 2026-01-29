# Change: Migrate Content Tools to New Renderer

**Parent Change**: unify-template-rendering

## Why
Content retrieval tools (`get_content`, `category_content`) currently use fragmented template rendering in `read_and_render_file_contents()`. Need to migrate to the new `render_template()` API for consistency and to leverage the unified rendering pipeline.

## What Changes
- Update `read_and_render_file_contents()` to use `render_template()` API
- Update content tools to handle `RenderedContent` objects
- Remove old rendering path from content utilities
- Ensure proper integration with template context and project flags

## Impact
- Affected specs: content-retrieval
- Affected code:
  - `src/mcp_guide/utils/content_utils.py` - Update `read_and_render_file_contents()`
  - `src/mcp_guide/tools/tool_content.py` - Handle `RenderedContent` in `get_content()`
  - `src/mcp_guide/tools/tool_category.py` - Handle `RenderedContent` in `category_content()`
