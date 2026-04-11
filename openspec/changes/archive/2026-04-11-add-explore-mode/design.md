# Design: Add Exploration Workflow Mode

## Purpose

This change introduces `exploration` as a first-class workflow phase without making it part of the standard ordered delivery sequence.

The key design constraint is:

```text
exploration is a mode of work
not a mandatory stage in the normal delivery pipeline
```

## Design Goals

1. Make research and requirement discovery explicit
2. Keep the existing ordered delivery phases intact
3. Preserve current issue context unless the user explicitly changes it
4. Make entry lightweight and exit consent-driven
5. Keep the phase guidance concise and behavior-focused

## Core Model

The workflow now has two different concepts:

```text
ordered delivery phases
  discussion -> planning -> implementation -> check -> review

available workflow phases
  discussion
  exploration
  planning
  implementation
  check
  review
```

`exploration` belongs to the second list, not the first.

## Phase Semantics

`exploration` should mean:

- investigate rather than implement
- inspect code, docs, and external references when useful
- compare options and clarify tradeoffs
- capture findings in OpenSpec artifacts if requested
- never write application code in this phase

It is intentionally close to `discussion`, but more explicitly research-oriented.

## Command Design

Add:

- `:workflow/explore`
- alias `:explore`

Behavior:

- no argument: retain current issue
- explicit argument: switch to that issue

This mirrors `:workflow/discuss`.

## Issue Handling

Exploration is not tightly coupled to issue identity.

### Explicit entry

If the user explicitly enters exploration:

- keep the current issue unchanged by default
- allow an optional issue argument to replace it
- use the retained issue as context where relevant

### Exploratory issue trigger

If the current issue starts with `explor`, the system should treat that as a hint that exploration mode may be appropriate.

Behavior:

- suggest the mode
- ask the user whether to enter it
- do not switch automatically

This keeps the workflow user-driven.

## Transition Rules

Entry into exploration may occur:

- via explicit command
- via explicit phase transition
- or via a system suggestion that the user accepts

Leaving exploration should require explicit consent.

That makes it parallel to other guarded transitions while preserving the exploratory stance.

## Template Design

### `_workflow/06-exploration.mustache`

This template should be short and principle-driven.

It should emphasize:

- think, investigate, compare
- use codebase and external references when needed
- OpenSpec artifacts are allowed
- implementation is not allowed

The template should avoid a rigid checklist.

### `_commands/workflow/explore.mustache`

This template should mirror the `discuss` command structure:

- retain current issue when no argument is supplied
- switch issue when an argument is supplied
- update the workflow phase to `exploration`

## Workflow Configuration

The workflow configuration needs to distinguish:

- allowed phases
- ordered phases
- consent rules

This change should:

- add `exploration` to the available/default phase set
- avoid placing it in the normal ordered sequence
- require explicit consent to leave it

## Rationale

This design is preferable to overloading `discussion` because it makes the no-implementation stance explicit while preserving the existing delivery flow.

It is preferable to inserting `exploration` into the ordered sequence because exploration is optional and situational, not a required delivery step.
