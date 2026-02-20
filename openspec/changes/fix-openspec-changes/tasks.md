## 1. Update OpenSpecTask Timer Behavior
- [x] 1.1 Remove `await self.request_changes_json()` call from `on_init()` method
- [x] 1.2 Simplify `_handle_changes_reminder()` to only invalidate cache (set `_changes_timestamp = None`)
- [x] 1.3 Remove `_changes_timer_started` flag and related logic (no longer needed)
- [x] 1.4 Update timer event handler to call simplified invalidation method

## 2. Update Tests
- [x] 2.1 Update `test_openspec_task.py` to reflect new timer behavior
- [x] 2.2 Remove tests for proactive changes request on startup
- [x] 2.3 Add test for cache invalidation on timer event
- [x] 2.4 Verify `:openspec/list` command still triggers on-demand requests

## 3. Verify Behavior
- [x] 3.1 Test that startup does not trigger changes request
- [x] 3.2 Test that `:openspec/list` command requests data when cache is empty
- [x] 3.3 Test that timer invalidates cache after TTL expires
- [x] 3.4 Test that subsequent `:openspec/list` requests fresh data after invalidation
