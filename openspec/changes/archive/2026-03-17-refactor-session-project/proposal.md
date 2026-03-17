# Change: Separate session identity from project context

## Why
`Session` currently conflates two concerns: the MCP client connection and the project
context. The ContextVar holds a `dict[str, Session]` keyed by project name, so switching
projects creates a new session — but the client connection hasn't changed. This also
forces MCP context (`CachedMcpContext`) into a separate module-level global, which breaks
correctness for HTTP transport with multiple concurrent clients.

A client retains the same session from start to end. Project changes occur within that
session.

## What Changes
- Unify `get_or_create_session` and `get_current_session` into a single `get_session()`
  function. Creates on first call, returns existing on subsequent calls. Never returns None.
- Change ContextVar from `dict[str, Session]` to a single `Optional[Session]`
- Project switching updates project fields on the existing session, not replacing it
- Move MCP context (agent_info, roots, client_params) from `CachedMcpContext` module
  global into `Session`
- Remove `CachedMcpContext`, `get_cached_mcp_context`, `set_cached_mcp_context`

## Impact
- Affected specs: `session-management`
- Affected code: `session.py`, `mcp_context.py`, all tool modules, `render/cache.py`,
  `prompts/guide_prompt.py`, `tools/tool_collection.py`, `discovery/commands.py`,
  `render/rendering.py`, plus ~35 test files
- **BREAKING**: None — internal refactor, no MCP tool API change
- Fixes correctness for HTTP transport (concurrent client isolation)
