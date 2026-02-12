# Change: Fix Content-Style Template Variables

**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

## Why

Templates currently use literal markdown formatting (`#`, `##`, `**`, `*`) instead of template variables (`{{h1}}`, `{{h2}}`, `{{b}}`, `{{i}}`). This means the `content-style` feature flag has no effect on template output, preventing users from controlling markdown rendering based on their agent's capabilities.

## What Changes

Convert all user-facing templates (non-agent/instruction and non-agent/information types) to use template variables for markdown formatting:
- Replace `#` through `######` with `{{h1}}` through `{{h6}}`
- Replace `**text**` with `{{b}}text{{b}}`
- Replace `*text*` with `{{i}}text{{i}}`

## Impact

- Affected files: ~60 template files in `src/mcp_guide/templates/`
- Templates will respect `content-style` flag (plain/headings/full)
- No breaking changes - default mode (plain) produces clean text output
- Users can now control markdown rendering based on agent capabilities
