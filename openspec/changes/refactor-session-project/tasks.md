## 1. Session model
- [ ] 1.1 Add `agent_info`, `roots`, `client_params` fields to `Session`
- [ ] 1.2 Ensure project switching updates project fields only, not session identity fields

## 2. MCP context wiring
- [ ] 2.1 Update `cache_mcp_globals` to write into the current session instead of module global
- [ ] 2.2 Update `_build_agent_context` to read agent info from session
- [ ] 2.3 Update `tool_utility.internal_client_info` to write agent info into session
- [ ] 2.4 Update all other `get_cached_mcp_context` / `set_cached_mcp_context` call sites

## 3. Cleanup
- [ ] 3.1 Remove `CachedMcpContext`, `get_cached_mcp_context`, `set_cached_mcp_context` from `mcp_context.py`
- [ ] 3.2 Remove `reset_cached_mcp_context` fixture from `tests/conftest.py` (no longer needed)

## 4. Tests
- [ ] 4.1 Update session tests to cover agent info persistence across project switches
- [ ] 4.2 Full test suite passes
