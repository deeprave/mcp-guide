# Design

## Context

Workflow-file content reaches `WorkflowMonitorTask` through the generic
file-content tool. The parser currently turns invalid state into `None`, the
monitor treats that as no renderable response, and the file-content tool falls
back to a generic receipt. The resulting session has no cached workflow state,
so later status or setup guidance asks for the same file again without
identifying the malformed field.

The state-format guidance is normally sent only after a valid submission, while
the initial startup instruction merely refers to it. That leaves agents without
the complete contract when they first create or relay the file.

## Goals / Non-Goals

**Goals:**

- Reject invalid submitted workflow state visibly and retain prior valid state.
- Supply the compact workflow-file contract before first submission.
- Keep the `issue`, `plan`, and `tracking` meanings consistent across all
  workflow guidance.

**Non-Goals:**

- Change the permissive workflow schema, add external tracker integration, or
  require an OpenSpec change in every project.
- Turn periodic or internal parsing callers into error-producing operations.
- Change direct-filesystem confirmation or workflow phase semantics.

## Decisions

### Opt into strict validation at the submitted-file boundary

The parser will retain its existing nullable result for passive callers and add
an explicit strict mode for the agent-submitted workflow-file path. Strict mode
will turn malformed YAML, non-mapping content, a missing `phase`, and schema
validation failures into concise validation errors.

This keeps existing monitoring and optional parsing behaviour compatible while
making the client-facing boundary reliable. Making every parser caller raise
would broaden the change and could turn background refreshes into failures.

### Preserve task failures through file-content aggregation

The generic file-content tool will return an unsuccessful aggregated task result
instead of replacing it with its generic receipt. This makes workflow
validation failures actionable at the same call that submitted the file.

Suppressing task failures or encoding them only in logs was rejected because it
recreates the silent retry loop.

### Provide the schema in initial startup guidance

Startup guidance is queued once when a workflow-enabled session starts, before
any workflow state is known. It includes the concise, strict YAML shape and
asks the agent to read the exact configured workflow-file path and submit its
complete content. If that direct read confirms the file is absent, the agent
creates it to record workflow state, initially using `phase: discussion` when
no other phase is selected. The guidance forbids discovery through globs,
repository searches, and tracked-file listings because those can omit ignored
dotfiles. The fuller state-format template remains the post-submission
reference. Both use the same field
semantics: `issue` is a dash-delimited, filesystem-friendly phrase identifying
the current work, `plan` is a relative path to an existing plan document, and
`tracking` is an optional external tracker string.

### Keep exploration available for every enabled workflow

`exploration` is a non-ordered phase used when requirements or alternatives
remain uncertain. The registered workflow-flag normaliser will append it to an
explicit list when it is absent, so setter-based configuration persists the
invariant. `parse_workflow_phases()` will apply the same idempotent workflow
helper as a read-time backstop for existing configuration written directly to
YAML. This is contained within workflow-specific code; generic flag setters
continue to dispatch through the normaliser registry.

## Risks / Trade-offs

- [Validation wording becomes a client-visible contract] → Return concise,
  field-specific errors where the correction is unambiguous and test the
  observable failure result.
- [Guidance copies drift] → Keep the schema compact, document the common
  semantics in the workflow specifications, and cover the resulting agent
  interaction rather than asserting template source text.
- [A valid old state may remain after a rejected submission] → Retaining it is
  intentional: an invalid update must not erase the last known workflow state.

## Migration Plan

No data migration is required. Existing valid workflow files continue to parse.
After deployment, an invalid submission receives a failure on that same tool
call; the agent corrects and resubmits the complete file.
