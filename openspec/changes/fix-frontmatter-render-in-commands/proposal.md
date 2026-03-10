# Change: Fix frontmatter template rendering in command results

## Why
Command results contain `instruction` and `description` fields with template placeholders (e.g., `{{tool_prefix}}`, `{{INSTRUCTION_AGENT_INSTRUCTIONS}}`) that are not being rendered. These fields should be processed through the template renderer before being returned to the agent.

Additionally, partial instructions (especially important ones with `^`) are being applied even when the partial isn't actually rendered into the template output. For example, `_client-info.mustache` has an important instruction that overrides the status command even though `{{>client-info}}` isn't included in the template.

## What Changes
- Identify where command results are constructed
- Wire template rendering for `instruction` and `description` fields
- Ensure template context is available (tool_prefix, agent instructions, etc.)
- Fix partial frontmatter merging to only apply when partial is actually rendered

## Impact
- Affected specs: command-system (if exists), tool-results
- Affected code: command handling, tool result processing, partial rendering
- **BREAKING**: None - this fixes existing broken functionality
