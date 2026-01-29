# Change: Migrate Command Rendering to New Renderer

## Why
Command help and execution currently use `render_file_content()` directly. Need to migrate to new `render_template()` function for consistency.

## What Changes
- Update `guide_prompt.py` to use `render_template()`
- Handle `RenderedContent` objects in command execution
- Convert rendered content to `Result` for command responses

## Impact
- Affected specs: command-system
- Affected code:
  - `src/mcp_guide/prompts/guide_prompt.py`
