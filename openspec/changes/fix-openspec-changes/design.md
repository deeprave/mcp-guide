## Context

`OpenSpecTask` already keeps a per-session changes cache and clears it after a
TTL. However, successful OpenSpec project detection still immediately queues a
client instruction to run `openspec list --json`. That makes an unrelated next
Guide response carry an OpenSpec task instruction.

## Goals / Non-Goals

**Goals:**

- Separate OpenSpec project detection from collection of change data.
- Make changes data lazy and invalidated by TTL or the client-reported
  `openspec/changes` modification time.
- Keep CLI availability, version, and project-structure detection unchanged.

**Non-Goals:**

- Changing the global `openspec-state` feature-flag contract.
- Polling the client filesystem or proactively refreshing changes data.
- Changing the behaviour of explicit OpenSpec commands other than their source
  of change-list data.

## Decisions

- Make the OpenSpec changes list demand-driven. The explicit OpenSpec list
  command renders one instruction to list `openspec/changes` and run
  `openspec list --json` when cached data is absent or invalid. Passive
  template-context construction never requests changes data.
- Store the list with its acquisition time and the `openspec/changes`
  modification time observed by the client. A later consumer reuses it only
  when both the TTL and modification-time checks succeed. This avoids a full
  list command when nothing changed while still responding promptly to local
  OpenSpec edits.
- Keep cached changes data owned by the active OpenSpec task, so a project
  switch or task restart retires it with the task.

## Risks / Trade-offs

- [A caller needs changes before the first cache fill completes] → retain the
  existing refresh instruction and render the normal pending response; do not
  manufacture an empty list.
- [Client metadata is unavailable] → treat the cache as invalid and request a
  fresh list, preserving correctness over reuse.
- [A command is rendered before changes data is available] → return the
  explicit refresh instruction without manufacturing an empty list.
