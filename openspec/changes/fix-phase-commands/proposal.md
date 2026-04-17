# Change: fix-phase-commands

## Why

The workflow command templates under
`src/mcp_guide/templates/_commands/workflow/` currently have two related
problems.

First, optional single-phase commands such as `plan`, `check`, and `review`
along with `explore`
omit `requires-workflow` entirely even though they reference phases that may
not be configured in a given workflow.

Second, the dynamic `phase` command accepts a runtime phase argument but does
not validate that argument against the configured workflow phases. Its current
`requires-workflow: true` frontmatter is correct for availability, but that
boolean requirement does not validate the requested phase name.

This leaves the command set structurally inconsistent and allows
`guide://_workflow/phase/<phase>` to rely on agent inference rather than an
explicit template-level validation path.

## Findings

The current command inventory relevant to this fix is:

- `plan.mustache` transitions to `planning` but has no `requires-workflow`
- `explore.mustache` should transition to `exploration` and should be gated on
  that phase being configured
- `check.mustache` transitions to `check` but has no `requires-workflow`
- `review.mustache` transitions to `review` but has no `requires-workflow`
- `phase.mustache` accepts a dynamic phase argument and uses
  `requires-workflow: true`, but has no explicit runtime validation for the
  requested phase

The following commands remain correctly modelled by `requires-workflow: true`
because they are valid whenever workflow is enabled, regardless of optional
phase configuration:

- `discuss.mustache`
- `implement.mustache`
- `explore.mustache`
- `reset.mustache`
- `issue.mustache`
- `show.mustache`

## What Changes

- Update optional single-phase workflow transition commands to declare
  `requires-workflow: [<phase>]` where the phase may be absent from a configured
  workflow
- Keep commands whose target phase is always valid when workflow is enabled on
  `requires-workflow: true`
- Add template-level runtime validation for `phase.mustache` so a requested
  phase must exist in the configured workflow before normal instructions are
  used
- Add workflow-scoped lambda support so templates can ask whether the current
  workflow contains a supplied phase name
- Add tests proving nested workflow lambdas work and that unavailable phases can
  raise template-level application errors

## Impact

- Affected specs:
  - `workflow-templates`
- Likely affected files:
  - `src/mcp_guide/templates/_commands/workflow/plan.mustache`
  - `src/mcp_guide/templates/_commands/workflow/explore.mustache`
  - `src/mcp_guide/templates/_commands/workflow/check.mustache`
  - `src/mcp_guide/templates/_commands/workflow/review.mustache`
  - `src/mcp_guide/templates/_commands/workflow/phase.mustache`
  - `src/mcp_guide/render/functions.py`
  - `src/mcp_guide/render/renderer.py`
  - `tests/test_template_functions.py`
- Breaking changes: None intended; this is a command metadata and validation fix
