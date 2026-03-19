## 1. Session registry (session.py)
- [x] 1.1 Add `WeakKeyDictionary` registry mapping `MiddlewareServerSession → Session`
- [x] 1.2 Add `register_session(mcp_session, session)` and `get_session_by_mcp_session(mcp_session)` helpers
- [x] 1.3 In `get_or_create_session`, register the session when `ctx` is available (`ctx.session`)
- [x] 1.4 Add `project_name_from_roots(roots)` helper to `mcp_context.py`

## 2. Notification plumbing (server.py)
- [x] 2.1 Add module-level `ContextVar[Optional[MiddlewareServerSession]]` for current notification session
- [x] 2.2 In `create_server()`, patch `mcp._mcp_server._handle_message` to set the ContextVar for `ClientNotification` messages
- [x] 2.3 Register `RootsListChangedNotification` handler on `mcp._mcp_server.notification_handlers`

## 3. Handler logic (server.py)
- [x] 3.1 Implement `_handle_roots_changed(notification)`:
  - Get `MiddlewareServerSession` from ContextVar
  - Look up guide `Session` from registry
  - Call `mcp_session.list_roots()` to get new roots
  - Update `session.roots`
  - If project name changed, call `session.switch_project(new_name)`
  - Invalidate template context cache

## 4. Tests
- [x] 4.1 Test roots change triggers project switch when project name differs
- [x] 4.2 Test no-op when roots unchanged (no switch, no cache invalidation)
