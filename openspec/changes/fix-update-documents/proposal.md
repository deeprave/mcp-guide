# Change: fix-update-documents

## Why

The current startup update prompting logic can tell the agent to run
`update_documents` even when the update should never be attempted.

The recent investigation exposed a specific bad path:

- the configured `docroot` existed
- `docroot` was the same path as the template source directory
- `{docroot}/.version` did not exist
- `McpUpdateTask` still queued the acknowledged update instruction
- the actual `update_documents` tool then failed because installer safety
  validation correctly rejects `docroot == template source`

That means the startup prompt path is currently missing the same gating that the
real updater already depends on.

This is undesirable for two reasons:

- it creates a false-positive update prompt for a configuration that should be
  treated as non-updatable
- it asks the agent to do work that is guaranteed to fail, which creates noise
  and weakens the value of acknowledged reminder-based update prompting

The intended behavior is stricter:

- no update prompt should be queued if `{docroot}/.version` does not exist
- no update prompt should be queued if `docroot` is the template source
  directory

The existing docroot safety check in the installer remains a good safety net,
but the startup prompt should be gated so it never asks the agent to run an
update in the first place.

## What Changes

- Change `McpUpdateTask` so startup prompting is skipped when the installed
  documentation version file is missing
- Apply the same docroot safety validation used by the installer before
  queuing any startup update instruction
- Treat invalid or non-updatable docroot states as "do not prompt" conditions,
  not as cases that should ask the agent to run `update_documents`
- Keep the installer-side docroot safety check in place as a defensive
  safeguard even after startup prompting is corrected

## Suggested Fix

The smallest coherent fix is:

- update `McpUpdateTask.handle_event()` to resolve `docroot`
- validate that `docroot` is safe for updates before any version comparison or
  prompt queuing
- read `{docroot}/.version`
- if the version file is missing, return without prompting
- only queue the acknowledged update instruction when:
  - `docroot` is valid for updates
  - the version file exists
  - the installed version differs from the package version

The preferred implementation should reuse the existing installer-side docroot
validation helper rather than duplicating the equivalence check in a second
form.

## Impact

- Affected specs:
  - likely `installation`
  - possibly `task-manager`
- Likely affected implementation:
  - `src/mcp_guide/tasks/update_task.py`
  - `src/mcp_guide/installer/core.py`
  - tests covering startup update prompting and docroot/version gating
- No user-facing syntax changes expected
