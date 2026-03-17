## 1. Unified session access (facade) ✅
- [x] 1.1 Add `get_session(ctx, *, project_name, _config_dir_for_tests)` that delegates to existing functions
- [x] 1.2 Migrate all `get_or_create_session` call sites in `src/` to `get_session`
- [x] 1.3 Migrate all `get_current_session` call sites in `src/` to `await get_session()`
- [x] 1.4 Remove `_get_session` / `_get_session_or_fail` helpers from `tool_collection.py`
- [x] 1.5 Migrate test imports and call sites
- [x] 1.6 Full test suite passes

## 2. Single-session ContextVar ✅
- [x] 2.1 Change `active_sessions` ContextVar from `dict[str, Session]` to `Optional[Session]`
- [x] 2.2 Update `get_session` internals: create on first call, return existing on subsequent
- [x] 2.3 Project switching updates project fields on existing session (not replacing it)
- [x] 2.4 Simplify `remove_current_session` (no project_name param, clears single ContextVar)
- [x] 2.5 Update tests that create multiple sessions per project
- [x] 2.6 Full test suite passes

## 3. MCP context into Session ✅
- [x] 3.1 Add `agent_info`, `roots`, `client_params` fields to `Session`
- [x] 3.2 Update `cache_mcp_globals` to write into current session
- [x] 3.3 Update all `get_cached_mcp_context` readers to use session fields
- [x] 3.4 Remove `CachedMcpContext`, `get_cached_mcp_context`, `set_cached_mcp_context`
- [x] 3.5 Remove `reset_cached_mcp_context` test fixture
- [x] 3.6 Full test suite passes
