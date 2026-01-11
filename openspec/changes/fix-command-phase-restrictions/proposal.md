# Fix Command Phase Restriction Enforcement

**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

## Why

Command templates with `requires-workflow-phase` restrictions are not being properly enforced. When a command is executed in a phase that doesn't match the restriction, the system should either:

1. Block the command entirely with an error message, or
2. Allow the command to execute normally

Currently, the system is doing neither - it's executing the command but only returning help text instead of processing the actual command arguments. This creates confusing behavior where users see the command "working" but not performing the intended action.

**Example Issue:**
- Template: `requires-workflow-phase: [discussion, planning]`
- Current phase: `review`
- Command: `:issue --tracking="JIRA GUIDE-153"`
- Expected: Command blocked with error message
- Actual: Command runs but shows help text instead of processing arguments

## What Changes

- Investigate and fix the phase restriction enforcement logic in command processing
- Ensure commands are either completely blocked or fully executed based on phase restrictions
- Add proper error messaging when commands are blocked due to phase restrictions
- Verify that `requires-workflow` and other `requires-*` directives work correctly

## Impact

- Affected specs: command-processing, workflow-commands
- Affected code: Command template processing system, phase validation logic
- **BREAKING**: May change behavior for commands that were previously showing help text instead of being blocked
