# Change: Fix frontmatter template rendering in command results

## Why
Command results contain `instruction` and `description` fields with template placeholders (e.g., `{{tool_prefix}}`, `{{INSTRUCTION_AGENT_INSTRUCTIONS}}`) that are not being rendered. These fields should be processed through the template renderer before being returned to the agent.

## What Changes
- Identify where command results are constructed
- Wire template rendering for `instruction` and `description` fields
- Ensure template context is available (tool_prefix, agent instructions, etc.)

## Impact
- Affected specs: command-system (if exists), tool-results
- Affected code: command handling, tool result processing
- **BREAKING**: None - this fixes existing broken functionality
