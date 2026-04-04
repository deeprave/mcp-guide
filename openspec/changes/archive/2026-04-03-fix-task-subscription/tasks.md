## 1. Fix dispatch_event subscription iteration
- [x] 1.1 Iterate a copy of `self._subscriptions` instead of the live list
- [x] 1.2 Remove the `active_subscriptions` accumulator and final overwrite

## 2. Fix timer loop session access
- [x] 2.1 Add `self._session` instance field to TaskManager
- [x] 2.2 Set `self._session` in `on_project_changed` callback
- [x] 2.3 Replace `get_active_session()` ContextVar lookup with `self._session` in timer loop
- [x] 2.4 Remove early `loop.create_task(self.start())` from `__init__`

## 3. Register TaskManager as SessionListener
- [x] 3.1 Add `session.add_listener(get_task_manager())` in `get_or_create_session`

## 4. Startup log buffering
- [x] 4.1 Add `StartupBufferingHandler` to `mcp_log.py`
- [x] 4.2 Call `flush_startup_buffer()` in `_configure_logging_after_fastmcp`

## 5. Timer loop resilience
- [x] 5.1 Split `_timer_loop` into wrapper with exception handling and `_timer_loop_inner`

## 6. Validation
- [x] 6.1 All 1738 tests pass without warnings
- [x] 6.2 Lint, type checks, formatting clean
- [x] 6.3 Manual verification: active tasks drop from 6 (peak) to 4 in steady state
- [x] 6.4 Timer events firing: RetryTask 57 runs, WorkflowMonitorTask 5 runs after ~58 minutes
- [x] 6.5 ClientContextTask and McpUpdateTask correctly unsubscribed
