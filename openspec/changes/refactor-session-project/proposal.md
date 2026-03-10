# Change: Separate session identity from project context

## Why
`Session` currently conflates two distinct concerns: the MCP client session (agent info,
roots, client params) and the project context (project name, categories, collections, flags).
Switching projects tears down and recreates the session, which is wrong — the client
connection hasn't changed. This also forces MCP context data (`CachedMcpContext`) to live
as a module-level global, which breaks correctness for HTTP transport with multiple
concurrent clients.

## What Changes
- Add session-scoped fields to `Session`: `agent_info`, `roots`, `client_params`
- `cache_mcp_globals` writes MCP context into the current session instead of a module global
- `_build_agent_context` reads agent info from the session
- Project switching updates `session.project_name` and reloads project data without
  replacing the session object
- Remove `CachedMcpContext`, `get_cached_mcp_context`, `set_cached_mcp_context` from
  `mcp_context.py` once all reads/writes go through `Session`

## Impact
- Affected specs: `session-management`
- Affected code: `src/mcp_guide/session.py`, `src/mcp_guide/mcp_context.py`,
  `src/mcp_guide/render/cache.py`, `src/mcp_guide/tools/tool_utility.py`,
  `src/mcp_guide/prompts/guide_prompt.py`
- **BREAKING**: None — internal refactor, no public API change
- Fixes correctness for HTTP transport (multiple concurrent clients each get their own
  session with their own agent info)
