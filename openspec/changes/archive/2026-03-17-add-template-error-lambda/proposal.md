# Change: Add `_error` template lambda for application-level errors

## Why
Command templates currently have no way to signal application-level errors back through the rendering pipeline. When a template detects an error condition (e.g., missing required argument), it renders the error message as normal content, which gets wrapped in `Result.ok()` — returning `success: true` for what is actually an error. This causes agents to misinterpret error messages as instructions to act on.

## What Changes
- Add `_error` template lambda to `TemplateFunctions` that accumulates error messages via a side-channel
- Add `errors: list[str]` field to `RenderedContent` to propagate template-signaled errors
- Update renderer to transfer accumulated errors from `TemplateFunctions` to `RenderedContent` after rendering
- Update `_execute_command` to check `rendered.errors` and return `Result.failure()` when non-empty
- Migrate existing command templates from inline error blocks to `{{#_error}}` lambda

## Impact
- Affected specs: template-support
- Affected code: `src/mcp_guide/render/functions.py`, `src/mcp_guide/render/renderer.py`, `src/mcp_guide/render/content.py`, `src/mcp_guide/prompts/guide_prompt.py`, command templates
