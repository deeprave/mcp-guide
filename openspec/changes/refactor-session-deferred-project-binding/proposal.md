# Change: Refactor Session To Support Deferred Project Binding

## Why

Server startup currently initializes the task manager before any MCP request context exists. That startup path reaches `get_session()`, which requires a reliable project name in order to load config.

This is a mismatch in lifecycle boundaries: process startup is happening before client-scoped roots are available. We do not want to guess from server cwd, and we also do not want `Session` to carry an optional `Project` because much of the codebase assumes a concrete project model is always present.

## What Changes

- Introduce a deferred project-binding model for `Session`
- Allow a session shell to exist before client roots or project name are known
- Fill the session's non-optional project slot with a dedicated placeholder project object rather than `None`
- Bind the real project/config only when a context-bearing operation first requires project identity
- Allow explicit project selection APIs such as `set_project(...)` to bootstrap an unbound session without first auto-resolving a project
- Split startup-time task manager initialization from project-bound initialization
- Ensure project-dependent listeners, flags, and caches initialize only after the real project is bound
- Preserve the invariant that `Session` always exposes a concrete project-like model, even before real project resolution

## Impact

**Affected specs:**
- `session-management` - session lifecycle gains explicit deferred binding state and binding semantics
- `task-manager` - startup must not require immediate project resolution
- `mcp-server` - server init and client/session init are distinguished more clearly

**Affected code:**
- `src/mcp_guide/session.py` - deferred binding lifecycle, placeholder project handling, explicit bind/ensure APIs
- `src/mcp_guide/task_manager/manager.py` - split server init from project-bound init
- `src/mcp_guide/server.py` - stop assuming task manager startup can resolve a project immediately
- `src/mcp_guide/mcp_context.py` - remain authoritative for client-derived project resolution, without adding server-cwd fallback
- Related tests covering startup, session creation, and first-access binding behavior

**Benefits:**
- Server startup no longer races ahead of MCP roots availability
- Project resolution remains grounded in client context rather than server process state
- Existing code can keep relying on a non-optional project model inside `Session`
- Multi-client semantics stay clearer because binding happens from real client context
