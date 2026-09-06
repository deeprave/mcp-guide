# ADR-012: Runtime-Owned Interaction Sessions

**Status:** Accepted
**Date:** 2026-08-29
**Supersedes:** ADR-006, ADR-009
**Related changes:** `upgrade-mcp-version`, `add-switch-roots`

## Context

The modern MCP protocol does not provide transport-owned application sessions.
Guide nevertheless needs isolated interaction state: a selected project root,
task queue, rendering cache, and client metadata. Historical ContextVar and
project-inference approaches allowed state to leak between requests and did
not define a reliable recovery path for a resumed interaction.

## Decision

- `GuideRuntime` owns the process registry of `Session` instances. Each
  registry entry is keyed by a FastMCP-validated explicit interaction ID, or
  by the retained legacy connection ID.
- A modern client binds by calling `set_project(path)`. Guide mints a FastMCP
  interaction ID when the client does not already supply one, binds the
  runtime-owned Session, and returns that ID in the successful result.
- An explicitly enabled local stdio request with an absolute inherited `PWD` follows the same
  binding operation. It mints and returns an interaction ID so all later
  requests are explicit and resumable.
- Other modern requests without an interaction ID are unbound and
  request-local. They cannot inherit or create cross-request state.
- Session and TaskManager ownership is explicit. Application code must pass
  the resolved Session; it must not recover one from ContextVar state.
- Session instances progress from unbound to bound to expiring, then disposal.
  Unbound request work uses the ephemeral collection; only successful initial
  binding promotes it to the active registry.
- `switch_project(name | path)` prepares a fresh Session and atomically replaces
  the active instance under the same public ID. The outgoing instance keeps its
  immutable project/root identity and finishes admitted work, including saves
  to its original project. Only connection metadata and establishment-log state
  transfer; caches, listeners, queues and tasks are fresh.
- Runtime keeps at most one expiring Session per public ID. Another switch,
  including a no-op selection, is rejected until disposal completes. No queued
  switches, historical reply routing or new client tokens are introduced.
- Requests retain and release their captured Session instance. New requests and
  delayed client replies resolve the active entry. Request completion never
  republishes an outgoing Session or updates the replacement's request accounting.
- Expiry stops new notifications and scheduling, then disposes of all owned
  resources after admitted work drains. Cleanup runs outside configuration
  locks. Failed disposal retains the expiring-ID guard; shutdown attempts every
  owned instance even if one cleanup fails.
- `ConfigManager` remains the sole owner of process configuration and docroot.
  `GuideRuntime` exposes a delegating façade for session construction without
  retaining a second docroot value.
- Shared configuration coordination and file locks remain. Registry replacement
  is a non-awaiting expected-instance check and publication; immutable Session
  bindings require no in-place transition locks or pre-switch reset callbacks.

## Consequences

- Concurrent interactions cannot observe each other's task queues, template
  caches, or selected projects.
- An invalid or expired interaction ID is reported as an invalid-session
  result. It is not reinterpreted as an unbound project and is never echoed.
- Direct unit tests must construct and pass a Session or a runtime-backed
  request context; ambient test setup is no longer a production contract.
