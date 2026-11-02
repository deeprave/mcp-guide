# Proposal

## Why

Agents can submit a syntactically valid `.guide.yaml` whose `tracking` field is
a mapping rather than the required string. Guide silently discards that invalid
state, acknowledges the file as though it succeeded, and later asks for the
workflow file again. This creates a persistent, confusing bootstrap loop and
does not tell the agent what it must correct.

## What Changes

- Provide the complete, compact workflow-file schema in startup guidance before
  an agent first submits the file.
- Define `issue` as a dash-delimited, filesystem-friendly current-work phrase,
  `plan` as a relative path to an existing plan document, and `tracking` as an
  optional, single-string external issue-tracker reference.
- Reject invalid workflow-file submissions with a clear error, without
  replacing cached valid state or acknowledging the submission as successful.
- Preserve existing tolerant parsing where callers deliberately use it, while
  allowing the workflow-file ingestion boundary to request a validation error.
- Align workflow discussion guidance and user documentation with the same
  field contract.
- Require agents to read the configured workflow-file path directly instead of
  using a glob, repository search, or tracked-file listing, which can omit the
  default ignored dotfile.
- Ensure every enabled workflow includes the non-ordered `exploration` phase,
  including explicit phase lists written through a flag setter or loaded from
  existing configuration.
- Reject submitted phases that are unknown or unavailable in the project's
  configured workflow, with a clear error that lists the available choices.
- Render only the configured workflow phases in bootstrap guidance.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `workflow-monitoring`: Invalid workflow-file content is rejected visibly and
  must not be treated as successfully received or cached.
- `workflow-context`: Bootstrap guidance for an uninitialised workflow supplies
  the strict workflow-file schema before asking an agent to submit it; enabled
  workflow phase lists always include `exploration`.
- `workflow-templates`: State-format and workflow discussion guidance describe
  the same `issue` and `tracking` field contract.
- `filesystem-tools`: File-content submission preserves a task failure as a
  tool failure rather than replacing it with a generic successful receipt.

## Impact

- Workflow parser and monitoring task, file-content result aggregation, and
  workflow startup/discussion/state-format templates.
- Workflow documentation and behavioural tests for invalid submitted state.
- No new dependencies, configuration fields, transport changes, or external
  issue-tracker integration.
