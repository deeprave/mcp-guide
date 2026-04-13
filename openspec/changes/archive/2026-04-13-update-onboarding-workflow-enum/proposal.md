# Change: Update Onboarding Workflow Enumeration

## Why

The onboarding prompt currently presents workflow choices in user-facing terms
that do not map cleanly onto workflow flag values accepted by the guide server.
That creates a mismatch between what the agent offers during onboarding and what
`set_project_flag("workflow", ...)` actually understands, which can lead to
invalid configuration attempts or inconsistent behavior.

The onboarding flow needs a defined enumeration of supported workflow modes and
an explicit mapping from the user-facing choice to the underlying `workflow`
flag value.

## What Changes

- Define the supported onboarding-facing workflow mode enumeration
- Specify the mapping from each onboarding choice to the existing `workflow`
  project flag model
- Clarify that `structured` is the boolean shorthand and `full` is the explicit
  full-sequence onboarding option
- Update onboarding behavior/specs so the agent presents only supported
  workflow options

The intended mapping is:

- `none` or `unstructured` -> `workflow: false`
- `structured` -> `workflow: true`
- `simple` -> `workflow: [discussion, implementation, exploration]`
- `developer` -> `workflow: [discussion, implementation, review, exploration]`
- `full` -> `workflow: [discussion, planning, implementation, check, review, exploration]`

This change also clarifies that `exploration` is not a normal ordered delivery
phase with a natural previous or next phase. It is a parallel exploratory mode
used for investigating approaches, testing alternatives, and often drafting
OpenSpec proposals, while remaining distinct from `discussion`, which is aimed
at alignment and scope clarification. `exploration` is available whenever
workflow is enabled, but it is not available when `workflow` is `false`.

## Impact

- Affected specs: `workflow-flags`
- Likely affected implementation:
  - `src/mcp_guide/templates/_commands/onboard.mustache`
  - any workflow-related help or onboarding text that describes workflow modes
- No new runtime concept is introduced beyond a defined onboarding mapping onto
  the existing `workflow` flag model
