# Change: Handle MCP roots/list_changed notifications

## Why
When connected to an IDE, the user may switch projects (e.g. open a different
workspace). The MCP protocol signals this via a `roots/list_changed` notification,
but mcp-guide currently ignores it. This means the session continues using the
original project context, serving stale content and flags.

CLI agents can also change working directory mid-session, triggering the same
notification.

## What Changes
- Register a handler for the `roots/list_changed` MCP notification
- On notification, re-extract roots from the MCP session
- Re-resolve the project name from the new roots
- If the project changed, call `switch_project` on the active session
- Update `session.roots` with the new roots list
- Invalidate caches that depend on project context

## Impact
- Affected specs: `session-management`
- Affected code: `server.py` or `startup.py` (handler registration),
  `mcp_context.py` (roots re-extraction), `session.py` (switch_project)
- **BREAKING**: None — additive behaviour, existing sessions unaffected
  when roots don't change
