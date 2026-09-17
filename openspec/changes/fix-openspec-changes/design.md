## Context

`OpenSpecTask` already keeps a per-session changes cache and clears it after a
TTL. However, successful OpenSpec project detection still immediately queues a
client instruction to run `openspec list --json`. That makes an unrelated next
Guide response carry an OpenSpec task instruction.

## Goals / Non-Goals

**Goals:**

- Separate OpenSpec project detection from collection of change data.
- Make changes data lazy, deduplicated while a refresh is pending, and
  invalidated by TTL or the client-reported `openspec/changes` modification
  time.
- Keep CLI availability, version, and project-structure detection unchanged.

**Non-Goals:**

- Changing the global `openspec-state` feature-flag contract.
- Polling the client filesystem or proactively refreshing changes data.
- Changing the behaviour of explicit OpenSpec commands other than their source
  of change-list data.

## Decisions

- Make the OpenSpec changes list demand-driven. The first context or command
  consumer with no valid cached data queues the existing client command once;
  concurrent consumers reuse that pending request rather than enqueuing
  duplicates.
- Store the list with its acquisition time and the `openspec/changes`
  modification time observed by the client. A later consumer reuses it only
  when both the TTL and modification-time checks succeed. This avoids a full
  list command when nothing changed while still responding promptly to local
  OpenSpec edits.
- Retain the existing acknowledgement and activation ownership for an
  on-demand request, so a project switch or task restart retires the pending
  request and cached data consistently.

## Risks / Trade-offs

- [A caller needs changes before the first cache fill completes] → retain the
  existing refresh instruction and render the normal pending response; do not
  manufacture an empty list.
- [Client metadata is unavailable] → treat the cache as invalid and request a
  fresh list, preserving correctness over reuse.
- [Several rendered consumers request changes together] → mark the refresh as
  pending before queuing it so exactly one request is delivered.
