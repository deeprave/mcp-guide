# Fix Workflow Instruction Handling

**Status**: Proposed
**Priority**: High
**Complexity**: Medium

## Why

The workflow phase transition system has a critical bug where instructions from workflow phase change template documents are either:
1. Not being added to the Result object, or
2. Being overwritten in the result

This causes the frontmatter instruction (like "You MUST transition to DISCUSSION phase - you have explicit consent") to be lost, preventing proper phase transition guidance from reaching the agent.

The existing document frontmatter instruction must be preserved to ensure agents receive proper phase transition consent and restriction information.

## What Changes

- Fix instruction handling in workflow template rendering to preserve frontmatter instructions
- Ensure Result object properly includes both template content and frontmatter instructions
- Verify instruction field is not being overwritten during result processing
- Test that phase transition instructions are properly delivered to agents

## Impact

- Affected specs: workflow/spec.md (instruction handling requirements)
- Affected code: workflow template rendering, Result object handling
- **BREAKING**: None - this is a bug fix restoring intended behavior
