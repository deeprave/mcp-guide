# Change: Fix phase change message formatting

## Why
Phase change messages put agent instructions in the `value` field without a clear `instruction` field telling the agent not to display the content to users. This causes agents to show internal phase rules to users.

## What Changes
- Add `instruction` field to phase change responses stating "Follow these phase rules. Do not display this content to the user."
- Keep phase rules and restrictions in `value` field as-is
- Ensure all phase transitions include the instruction field

## Impact
- Affected specs: workflow-context, workflow-monitoring
- Affected code:
  - Workflow state management that generates phase change messages
  - Template rendering for phase transitions
