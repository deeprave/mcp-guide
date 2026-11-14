# Proposal

## Why

Projects that select an issue tracker can still commit work without an issue identifier, which weakens traceability between delivered changes and their planning records. The selected tracker policy must make the expectation explicit while retaining scope-based defaults and a user-directed exception for a specific change.

## What Changes

- Make the selected issue-tracking provider policy require an issue identifier for eligible changes.
- Update the selected-tracker policy guidance so small bug fixes and non-OpenSpec-tracked changes default to untracked, OpenSpec-tracked non-bug-fix changes default to tracked, and unclear cases ask the user.
- Allow the user to waive tracking for a specific change without changing the project policy.
- Instruct agents to create a corresponding issue when needed and supported, and allocate the issue to the active change or commit.
- Place the new commit-flow guidance before the branch-format instruction in the commit template.

## Capabilities

### New Capabilities

- `issue-tracking-policy`: Commit-time guidance for requiring an issue identifier when a project has a known tracker.

### Modified Capabilities

None.

## Impact

- The `git-commit` skill
- Issue-tracking policy templates and their shared content
