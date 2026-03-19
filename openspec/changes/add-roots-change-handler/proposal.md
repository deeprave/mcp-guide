# Change: Handle MCP roots/list_changed notifications

## Why
When connected to an IDE, the user may switch projects (e.g. open a different
workspace). The MCP protocol signals this via a `roots/list_changed` notification,
but mcp-guide currently ignores it. This means the session continues using the
original project context, serving stale content and flags.

CLI agents can also change working directory mid-session, triggering the same
notification.

## Dependency
This change **must be implemented after `migrate-to-standalone-fastmcp`**.

The vendored `mcp` SDK (v1.26.0) registers notification handlers on a singleton
low-level `Server` instance with no session context — making it impossible to
identify which client sent the notification in a multi-client HTTP scenario.

The standalone FastMCP (PrefectHQ/fastmcp v3) solves this via the `on_notification`
middleware hook, which provides a `MiddlewareContext` with `fastmcp_context`
carrying per-client session identity (`session_id`, `client_id`). It also opens
the door to authentication and other HTTP-transport features that are important
for mcp-guide's shared-resource use case.

## What Changes
- Register an `on_notification` middleware hook for `notifications/roots/list_changed`
- On notification, re-extract roots from the MCP session via `fastmcp_context`
- Re-resolve the project name from the new roots
- If the project changed, call `switch_project` on the active session
- Update `session.roots` with the new roots list
- Invalidate caches that depend on project context

## Impact
- Affected specs: `session-management`
- Affected code: `server.py` or `startup.py` (middleware registration),
  `mcp_context.py` (roots re-extraction), `session.py` (switch_project)
- **BREAKING**: None — additive behaviour, existing sessions unaffected
  when roots don't change
- **Prerequisite**: `migrate-to-standalone-fastmcp` must be completed first
