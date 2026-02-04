# Change: Migrate Command Rendering to render_template() API

**Parent Change**: unify-template-rendering

## Why
Command execution in `guide_prompt.py` currently uses `render_file_content()` directly and accesses frontmatter dict for metadata. Need to migrate to the new `render_template()` API for consistency and add typed properties to `RenderedContent` for cleaner metadata access.

## What Changes
- Add properties to `RenderedContent` for common frontmatter items (description, usage, category, aliases)
- Update `handle_command()` to use `render_template()` API
- Handle `RenderedContent` return type and extract instruction property
- Use new properties instead of accessing frontmatter dict directly
- Update exception handling to catch and log rendering errors
- Remove redundant instruction rendering (now handled by API)
- Ensure help system continues to work

## Impact
- Affected specs: command-system
- Affected code:
  - `src/mcp_guide/render/content.py` - Add properties to `RenderedContent`
  - `src/mcp_guide/prompts/guide_prompt.py` - Update command rendering and instruction handling
