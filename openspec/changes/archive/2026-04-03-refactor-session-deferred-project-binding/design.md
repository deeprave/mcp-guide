## Context

`mcp-guide` currently couples session creation with project resolution. That works during tool execution, where an MCP `Context` is available and roots can be queried, but it breaks during process startup because `@mcp.on_init()` runs before any client session context exists.

The immediate symptom is that task manager startup calls `get_session()`, which calls `resolve_project_name()`, which fails because roots have not yet been cached. The deeper issue is architectural: server lifecycle code is trying to force creation of a client/project-bound session.

At the same time, the current design prefers a non-optional `Project` model in `Session`. We want to preserve that invariant because much of the code assumes it can access project fields without threading `Optional[Project]` through the system.

## Goals / Non-Goals

**Goals:**
- Decouple session object creation from real project resolution
- Preserve a non-optional project slot within `Session`
- Avoid using server cwd as a proxy for client cwd
- Make startup safe before MCP roots are available
- Make project-bound initialization happen only when real client context exists

**Non-Goals:**
- Changing the project name detection priority defined in ADR 009
- Treating server startup as equivalent to client session activation
- Making project access optional throughout the codebase
- Solving all multi-client lifecycle issues beyond the session/project binding boundary

## Decisions

### Use a Placeholder Project Instead of `Optional[Project]`

**Decision:** `Session` will always hold a concrete project model, but before binding it will be a dedicated placeholder wrapper around a project representing "unbound project".

**Rationale:**
- Preserves the existing invariant that `Session` has a project object
- Avoids spreading `Optional[Project]` checks through the codebase
- Makes the unbound state explicit and inspectable

**Constraints:**
- The placeholder must be distinguishable from a real persisted project
- The placeholder must not be accidentally saved as a real project config
- The placeholder should mimic real project behavior where safe and appropriate
- Operations that require a real bound project should raise the existing `NoProjectError` path, or allow it to bubble where that behavior already exists
- `Session` constructor flow should no longer require a real `Project` argument up front; it should initialize `self.__project` with the unbound wrapper and replace it on bind
- Persistence and config-write paths require explicit guards so an unbound project can never be serialized, saved, renamed, or otherwise treated as a real stored project

### Add Explicit Project Binding To Session

**Decision:** Introduce an explicit bind step such as `ensure_project_bound(ctx)` or equivalent that resolves the real project and swaps the placeholder for the persisted project config.

**Rationale:**
- Makes project-bound operations intentional
- Allows server startup to create runtime/session structures without requiring roots yet
- Centralizes the transition from placeholder to real project

**Binding rule:** Any tool, prompt, or resource access that has a valid MCP context and updates the session's cached MCP context should trigger project binding if the active project is still unbound and the roots list is sufficient to resolve a real project.

### Split Server Init From Project-Bound Init

**Decision:** Task manager initialization will occur in two phases:
- server init: registration and project-independent setup
- project-bound init: flag loading, project-sensitive task setup, and any work that requires a real session project

**Rationale:**
- Matches the real lifecycle boundaries of an MCP server
- Prevents startup from trying to infer client context prematurely
- Avoids blocking startup on future request context that may never arrive

### Require Real Client Context For Binding

**Decision:** The first real bind must be driven by client-derived context or an explicit project name, not server cwd.

**Rationale:**
- Preserves ADR 009: server cwd is not the client cwd
- Keeps multi-client behavior sane
- Avoids binding a process-global guess that could leak across sessions

### Make `set_project(...)` A Valid Bootstrap Path

**Decision:** Explicit project-selection flows such as `set_project(project_name)` must be able to create or adopt an unbound session and bind it directly to the requested project, without first calling auto-resolution.

**Rationale:**
- `set_project(...)` is the operator-controlled recovery path when automatic project detection is unavailable
- If `set_project(...)` internally depends on `get_session()` auto-resolution first, the recovery path is broken
- Explicit project choice is a stronger signal than any fallback inference and should bypass detection

## Risks / Trade-offs

**Risk:** Placeholder project leaks into behavior that assumes a real persisted project
- **Mitigation:** Make placeholder identity explicit and add guards at persistence and config-write boundaries so unbound state either raises `NoProjectError` or is intentionally ignored where no-op behavior is correct

**Risk:** Some listeners or caches may initialize too early against the placeholder
- **Mitigation:** Separate server init from project-bound init, and delay project-sensitive listener behavior until after binding

**Risk:** Project-change notifications may become ambiguous during initial bind
- **Mitigation:** Reuse the existing real-project load notification on first bind, and suppress project-related events while the session remains unbound

**Trade-off:** Session lifecycle becomes more explicit and slightly more complex
- **Benefit:** Lifecycle boundaries become correct and startup errors stop depending on unavailable context

## Migration Plan

1. Introduce wrapper-based placeholder project semantics and explicit session binding API
2. Update task manager startup to avoid immediate project resolution
3. Trigger binding from any context-bearing tool, prompt, or resource access when valid roots are available
4. Make `set_project(...)` bootstrap an unbound session directly from the explicit project name
5. Add tests for startup-before-context, explicit-project binding, and first-context binding
6. Add guards at all persistence and config-write boundaries that might otherwise accept an unbound project
7. Validate that placeholder state never persists to config

## Open Questions

None. Placeholder shape, binding trigger, and event behavior are defined by this change.
