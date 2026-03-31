# Fix Task Subscription Lifecycle

**Status**: Complete
**Priority**: High
**Complexity**: Medium

## Why

After the deferred-session refactor, the TaskManager timer loop never dispatched events. The status display showed 6 active tasks permanently with `Runs 0` — tasks that should have unsubscribed (like `ClientContextTask` when `allow-client-info` is disabled) never got the chance.

## Root Cause

**TaskManager was never registered as a SessionListener.** `on_project_changed` existed on `TaskManager` but was only registered lazily inside `resolved_flags()` — which itself requires a `TIMER_ONCE` dispatch, which requires `project_bound=True`, which requires the session. A chicken-and-egg dependency meant the timer loop spun forever with `project_bound=False` and never dispatched.

Before the deferred-session refactor, `project_is_bound` was hardcoded `True`, so this registration gap was invisible. The refactor made `project_is_bound` reflect real state, exposing the missing listener.

## Contributing Issues

- **ContextVar isolation**: The timer loop (a background `asyncio.Task`) used `get_active_session()` which reads a `ContextVar` — always `None` in the timer task's context. Replaced with an instance-level `self._session` reference set via the now-working `on_project_changed` callback.
- **dispatch_event overwriting unsubscribe**: The iteration built an `active_subscriptions` list and reassigned `self._subscriptions` at the end, restoring any subscriber that had unsubscribed during dispatch. Fixed by iterating a copy instead.
- **Early startup logs lost**: `@task_init` decorators fire at import time before logging handlers exist. Added a `StartupBufferingHandler` to capture and replay early log records — this was essential for diagnosing the above issues.

## What Changed

- **session.py**: Register `TaskManager` as a session listener in `get_or_create_session`
- **manager.py**: Add `self._session` field set via `on_project_changed`; use it in timer loop instead of `get_active_session()` ContextVar; remove early `loop.create_task(self.start())` from `__init__`; iterate copy in `dispatch_event`; split `_timer_loop` with exception handling wrapper
- **mcp_log.py**: `StartupBufferingHandler` + `flush_startup_buffer()`
- **server.py**: Call `flush_startup_buffer()` after logging configured
