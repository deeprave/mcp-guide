# Proposal

## Why

Projects that select an issue tracker can still commit work without an issue identifier, which weakens traceability between delivered changes and their planning records. Teams that require issue-backed commits need an optional policy that makes the expectation explicit while retaining a user-directed exception.

## What Changes

- Add an optional issue-tracking policy that onboarding can offer when a recognised issue tracker is selected.
- Update the selected-tracker policy guidance so commits require a tracking identifier unless the user explicitly says one is unnecessary.
- Instruct agents to create a corresponding issue when needed and supported, and allocate the issue to the active change or commit.
- Place the new commit-flow guidance before the branch-format instruction in the commit template.

## Capabilities

### New Capabilities

- `issue-tracking-policy`: Optional configuration and commit-time guidance for requiring an issue identifier when a project has a known tracker.

### Modified Capabilities

None.

## Impact

- `src/mcp_guide/templates/_commands/onboard.mustache`
- `src/mcp_guide/templates/_commands/git/commit.mustache`
- Issue-tracking policy templates and their shared content
- Behaviour-focused tests for rendered guidance and policy selection
