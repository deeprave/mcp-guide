# Change: fix-phase-commands

## Why

The workflow command templates under
`src/mcp_guide/templates/_commands/workflow/` are inconsistent with the
intended meaning of `requires-workflow`.

For these command templates, `requires-workflow: [phase]` is intended to
validate that referenced workflow phases are valid configured phases. It is not
meant to mean "render only when the current phase equals this value", and it is
not interchangeable with the generic boolean form `requires-workflow: true`.

The current templates do not follow that contract:

- `discuss.mustache`, `explore.mustache`, `reset.mustache`, and
  `phase.mustache` use `requires-workflow: true`
- `plan.mustache`, `implement.mustache`, `check.mustache`, and
  `review.mustache` omit `requires-workflow` entirely
- older workflow templates such as `_workflow/05-review.mustache` already use
  phase-list syntax, so command templates are not internally consistent

This creates a structural bug in command metadata. Phase-changing commands are
supposed to declare the workflow phases they reference so invalid or drifted
phase names are caught by the template/frontmatter contract. Using `true` or
omitting the field bypasses that validation and leaves the command set
inconsistently specified.

## Findings

The current command inventory is:

- `discuss.mustache` transitions to `discussion` but declares
  `requires-workflow: true`
- `explore.mustache` transitions to `exploration` but declares
  `requires-workflow: true`
- `plan.mustache` transitions to `planning` but has no `requires-workflow`
- `implement.mustache` transitions to `implementation` but has no
  `requires-workflow`
- `check.mustache` transitions to `check` but has no `requires-workflow`
- `review.mustache` transitions to `review` but has no `requires-workflow`
- `reset.mustache` transitions to `discussion` but declares
  `requires-workflow: true`
- `phase.mustache` accepts a dynamic phase argument but declares
  `requires-workflow: true`

The non-transition helpers `issue.mustache` and `show.mustache` also use
`requires-workflow: true`, which may still be correct for those templates
because they require workflow to exist but do not encode a specific phase
target.

## What Changes

- Update each single-phase workflow transition command template to declare the
  relevant phase using `requires-workflow: [<phase>]`
- Audit `reset.mustache` and treat it as a transition to `discussion` for
  frontmatter validation purposes
- Define the expected handling for `phase.mustache`, which takes a dynamic phase
  argument and therefore cannot be fully represented by a single hardcoded
  phase list without additional validation support
- Keep generic workflow-required helpers such as `show` and `issue` on the
  boolean form unless their semantics are intentionally narrowed
- Add tests or validation coverage proving the command templates declare
  phase-list requirements consistently

## Impact

- Affected specs:
  - `workflow-templates`
- Likely affected files:
  - `src/mcp_guide/templates/_commands/workflow/discuss.mustache`
  - `src/mcp_guide/templates/_commands/workflow/explore.mustache`
  - `src/mcp_guide/templates/_commands/workflow/plan.mustache`
  - `src/mcp_guide/templates/_commands/workflow/implement.mustache`
  - `src/mcp_guide/templates/_commands/workflow/check.mustache`
  - `src/mcp_guide/templates/_commands/workflow/review.mustache`
  - `src/mcp_guide/templates/_commands/workflow/reset.mustache`
  - `src/mcp_guide/templates/_commands/workflow/phase.mustache`
- Breaking changes: None intended; this is a metadata/spec correctness fix
