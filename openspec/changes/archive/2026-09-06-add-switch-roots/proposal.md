## Why

Agents need to change project roots without losing their public Guide session ID.
Replacing the bound Session, rather than resetting and rebinding it in place,
isolates old work from new project state through ordinary object ownership.

## What Changes

- Retain `switch_project(name | path)`: exactly one selector; name-only keeps the
  current root, while path-only derives the name from the normalised new root.
  The tool description continues to say it can **rebind the project root**.
- Replace the in-place transition design with the Session lifecycle
  `unbound -> bound -> expiring`. Unbound Sessions are ephemeral; bound Sessions
  are retained by validated public ID; expiring Sessions finish existing work
  and are disposed of.
- Create a fresh bound Session for a different project selection, keep the
  public `session_id`, and atomically replace runtime's active entry. Each
  individual bound Session keeps its original project/root identity.
- Keep at most one expiring Session for an ID. Reject another switch while that
  ID is expiring, without changing either existing instance.
- Let in-flight work finish against its original Session, including legitimate
  saves to that Session's original project. New requests, including client
  replies, use the current bound Session.
- Initialise fresh caches, task state, listeners and instruction queues. Transfer
  only the public ID and connection-level metadata; do not transfer project state.
- Centralise promotion, replacement, request ownership and disposal in runtime.
  Remove transition-only reset machinery and locking made unnecessary by
  immutable per-instance binding; retain shared configuration locking.
- Preserve initial `set_project(path)`, path normalisation and modern/legacy MCP
  identity contracts. Preserve the one-time negotiated-protocol establishment
  log without treating internal Session replacement as a new client session.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guide-project-tools`: root rebinding and name selection through fresh-session
  replacement, with unchanged public ID and an expiring-ID rejection.
- `session-management`: ephemeral, bound and expiring Session ownership,
  immutable per-instance bindings, completion and disposal.
- `request-context`: each request holds its resolved Session instance; switch
  response processing explicitly uses the replacement.
- `mcp-v2-request-context`: the public ID resolves the current bound instance,
  preserves protocol compatibility and logs establishment only once.

## Impact

- Affected code: runtime Session registries and request leases, Session binding
  and configuration access, TaskManager shutdown, request/result adapters,
  project tools and lifecycle tests.
- Existing in-place-rebinding code and tests in the worktree are superseded
  where they conflict with this design. Compatible selector/path handling is
  reused; the revised task checklist must be completed before claiming readiness.
- No new dependency, public session token, wire-level reply correlation,
  configuration-file format change or persisted-data migration.
- Deferred `fix-client-resolution` and `pytest-maintenance` work remains separate.
  This change is not a general concurrent-configuration editing redesign.
