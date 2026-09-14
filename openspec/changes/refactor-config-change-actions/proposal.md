## Why

Configuration publication currently tells affected sessions only that "something"
changed.  Listeners consequently invalidate broadly and the Session-owned
TaskManager restarts all project tasks, even when the relevant configuration
area did not change.  That loses the precision required for concurrent sessions
sharing configuration and makes future configuration-driven features harder to
add safely.

## What Changes

- Introduce a typed configuration snapshot-delta notification describing the
  old and new validated configuration images, followed by a per-session
  effective update describing the scoped differences relevant to one bound
  session.
- Make GuideRuntime the active-session selection boundary and Session the
  registration and dispatch boundary for configuration-update consumers,
  including its template cache and TaskManager.
- Refactor configuration publication from internal writes and external watcher
  changes so ConfigManager publishes snapshot deltas without registering or
  handling sessions, while GuideRuntime computes and dispatches per-session
  effective updates.
- Refactor TaskManager configuration handling to apply only affected lifecycle,
  cache, instruction, and event-subscription changes rather than
  unconditionally restarting all project tasks. State produced by a handler
  that is stopped or replaced is retired, while valid state owned by unaffected
  handlers remains available.
- Replace ambient task ownership and lifecycle-generation inference with one
  explicit `TaskActivation` capability per project-task instance. The
  activation owns that task's subscriptions, cached values, instructions, and
  deferred delivery callbacks, and rejects writes after retirement.
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
  publication, `task_manager/manager.py`, task protocols and implementations,
  render cache, and configuration/lifecycle tests.
- Existing listener implementations migrate from `on_config_changed(session)`
  to the new configuration-update protocol.
- ConfigManager no longer owns a Session registry or performs session
  lifecycle work.
- No external MCP tool contract or dependency change is expected.
