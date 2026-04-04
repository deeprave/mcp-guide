# Change: Add Exploration Workflow Mode

## Why

The current workflow supports a semi-ordered set of phases:

- discussion
- planning
- implementation
- check
- review

That covers scoped delivery well, but it does not model open-ended research cleanly. In practice there is a recurring need for a mode that is explicitly for:

- clarifying ideas
- investigating problems
- gathering requirements
- exploring code and external references
- capturing findings in OpenSpec artifacts

without implying that implementation should begin.

Today this behavior is approximated with `discussion`, but the distinction matters:

- exploration is not part of the normal ordered delivery sequence
- exploration should explicitly prohibit implementation
- exploration should be easy to enter and leave without disrupting the active issue unless the user wants that

## What Changes

### 1. Add a new workflow phase: `exploration`

Add `exploration` as a supported workflow phase.

This phase is:

- non-ordered
- research-oriented
- close to `discussion`, but more explicit about investigation and requirement discovery
- explicitly non-implementing

### 2. Add a dedicated workflow command

Add a new command template:

- `_commands/workflow/explore.mustache`

with alias:

- `explore`

The command should follow the same pattern as `:workflow/discuss`:

- `:workflow/explore`
  - retain the current issue
- `:workflow/explore <issue>`
  - switch to the provided issue

### 3. Add a dedicated phase template

Add:

- `_workflow/06-exploration.mustache`

The phase guidance should be concise and stance-oriented. It should emphasize:

- think and investigate rather than implement
- inspect the codebase and other sources when useful
- compare options and clarify requirements
- use OpenSpec artifacts to capture thinking when asked
- do not write application code while in this phase

### 4. Treat exploration as independent from normal issue sequencing

Exploration is not bound tightly to workflow issue identity.

Rules:

- if exploration is entered explicitly, the current issue remains unchanged unless an issue argument is provided
- the retained issue may be used as context for the exploration
- switching into exploration must not automatically discard or overwrite the active issue

### 5. Recognize exploratory OpenSpec issues as a suggestion trigger

If the current issue starts with `explor`, that should be treated as a signal that exploration mode may be appropriate.

The system should:

- suggest exploration mode
- ask the user whether to enter it
- not switch automatically

### 6. Require explicit consent to exit exploration

Like other consent-gated transitions, leaving `exploration` should require explicit user agreement.

### 7. Add exploration to workflow configuration

The workflow feature-flag and default phase set should include `exploration`, but it should not be sequenced as part of the standard ordered delivery flow.

## Scope

In scope:

- workflow phase support for `exploration`
- `:workflow/explore` and alias `:explore`
- dedicated phase template
- trigger suggestion for exploratory issue names
- consent rules for leaving exploration
- workflow configuration updates

Out of scope:

- changing the ordered delivery sequence itself
- implementation of application features while in exploration
- broad redesign of workflow beyond what is needed to support this phase

## Success Criteria

- `exploration` can be entered explicitly as a workflow phase
- `:workflow/explore` mirrors `:workflow/discuss` issue-handling behavior
- exploration guidance clearly forbids implementation and allows OpenSpec-only capture
- the workflow system can suggest exploration mode when the current issue is exploratory
- leaving exploration requires explicit consent
- the default workflow config includes exploration without forcing it into the ordered phase sequence

## Impact

- Affected specs:
  - `workflow-flags`
  - `workflow-context`
  - `help-template-system`
- Affected code:
  - workflow phase parsing and validation
  - workflow command templates
  - workflow phase templates
  - any workflow transition logic that assumes only the current ordered phase list
