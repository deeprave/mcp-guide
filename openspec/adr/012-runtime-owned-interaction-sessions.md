# ADR-012: Runtime-Owned Interaction Sessions

**Status:** Accepted
**Date:** 2026-08-29
**Supersedes:** ADR-006, ADR-009
**Related change:** `upgrade-mcp-version`

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
- A local stdio request with an absolute inherited `PWD` follows the same
  binding operation. It mints and returns an interaction ID so all later
  requests are explicit and resumable.
- Other modern requests without an interaction ID are unbound and
  request-local. They cannot inherit or create cross-request state.
- Session and TaskManager ownership is explicit. Application code must pass
  the resolved Session; it must not recover one from ContextVar state.
- `ConfigManager` remains the sole owner of process configuration and docroot.
  `GuideRuntime` exposes a delegating façade for session construction without
  retaining a second docroot value.

## Consequences

- Concurrent interactions cannot observe each other's task queues, template
  caches, or selected projects.
- An invalid or expired interaction ID is reported as an invalid-session
  result. It is not reinterpreted as an unbound project and is never echoed.
- Direct unit tests must construct and pass a Session or a runtime-backed
  request context; ambient test setup is no longer a production contract.
