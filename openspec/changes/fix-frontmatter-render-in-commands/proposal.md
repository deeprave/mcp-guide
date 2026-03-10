# Change: Fix partial instruction handling in template rendering

## Why
Two related bugs in partial frontmatter handling:

1. **Partial instruction applied when partial not rendered** — `renderer.py` collects partial frontmatter based on whether the partial has content, not whether chevron actually rendered it. If `{{>client-info}}` isn't in the template body, chevron never uses it, but its frontmatter (including important `^` instructions) still gets collected and applied. This causes the status command to be overridden by the `_client-info` partial's instruction even though it isn't included.

2. **Partial instruction fields not rendered as templates** — partial `instruction`/`description` fields are loaded raw and never passed through chevron with the template context, so placeholders like `{{INSTRUCTION_AGENT_INSTRUCTIONS}}` and `{{tool_prefix}}` remain unresolved.

## What Changes
- Track which partials chevron actually accesses during rendering; only collect frontmatter from those
- Render partial `instruction`/`description` fields through chevron with the current context when loading

## Impact
- Affected code: `src/mcp_guide/render/renderer.py`
- **BREAKING**: None — fixes broken/incorrect behaviour only
- Deliberately avoids broader frontmatter centralisation refactor to minimise risk
