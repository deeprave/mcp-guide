## Why

The OpenSpec task still queues an `openspec list --json` request as soon as it
detects an OpenSpec project. This obsolete eager behaviour interrupts unrelated
work and needlessly asks the client for information that may never be used.

## What Changes

- Remove automatic OpenSpec changes-list requests from task initialisation and
  project detection.
- Fetch the changes list only when a feature requires it and no valid cached
  result is available.
- Retain the per-session changes cache until its TTL expires or the client
  reports that the `openspec/changes` directory has changed.
- Preserve existing OpenSpec CLI, version, and project-structure checks.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `template-context`: Supply OpenSpec changes through an on-demand,
  invalidation-aware cache rather than an automatic background request.
- `task-manager`: Prevent project task initialisation from queuing unrelated
  OpenSpec changes-list work.

## Impact

- `OpenSpecTask`, its change-list request template, and cache invalidation.
- OpenSpec command and template-context consumers that require change data.
- Focused task and template-context behaviour tests.
