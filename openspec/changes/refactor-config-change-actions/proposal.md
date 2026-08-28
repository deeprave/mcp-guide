## Why

Configuration publication currently tells affected sessions only that "something"
changed.  Listeners consequently invalidate broadly and the Session-owned
TaskManager restarts all project tasks, even when the relevant configuration
area did not change.  That loses the precision required for concurrent sessions
sharing configuration and makes future configuration-driven features harder to
add safely.

## What Changes

- Introduce a typed configuration-update notification describing the old and
  new effective configuration and the scoped differences relevant to one
  bound session.
- Make Session the registration and dispatch boundary for configuration-update
  consumers established when it binds, including its template cache and
  TaskManager.
- Refactor configuration publication from internal writes and external watcher
  changes to compute per-session diffs before notifying consumers.
- Refactor TaskManager configuration handling to apply only affected lifecycle,
  cache, and event-subscription changes rather than unconditionally restarting
  all project tasks.
- Define consumer error isolation, ordering, and coalescing so concurrent
  publications leave each session at the latest effective configuration.

## Capabilities

### New Capabilities

- `configuration-update-actions`: Per-session configuration diff, registration,
  dispatch, and consumer-application protocol.

### Modified Capabilities

- `config-management`: Configuration file and in-process publications provide
  scoped effective changes to active sessions.
- `task-manager`: Task lifecycle and cache handling responds selectively to
  configuration changes.

## Impact

- Affected code: `session.py`, `session_listener.py`, runtime configuration
  publication, `task_manager/manager.py`, render cache, and configuration
  tests.
- Existing listener implementations migrate from `on_config_changed(session)`
  to the new configuration-update protocol.
- No external MCP tool contract or dependency change is expected.
