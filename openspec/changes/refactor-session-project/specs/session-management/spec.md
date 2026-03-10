## MODIFIED Requirements

### Requirement: MCP Context Deduplication
The system SHALL store MCP session context (agent info, roots, client params) on the
`Session` object rather than in a separate module-level global.

#### Scenario: Session carries MCP context
- WHEN MCP context is cached via `cache_mcp_globals()`
- THEN agent_info, roots, and client_params are stored on the current `Session` instance
- AND no separate `CachedMcpContext` module global is used

#### Scenario: Project switch preserves session context
- WHEN the active project is switched
- THEN session identity fields (agent_info, roots, client_params) are preserved
- AND only project-scoped fields (project_name, categories, collections, flags) are updated

#### Scenario: Concurrent HTTP clients isolated
- WHEN multiple clients connect via HTTP transport
- THEN each client has its own `Session` instance
- AND agent info for one client does not affect another client's session

#### Scenario: Consolidated extraction
- WHEN session is created via `get_or_create_session()`
- THEN `cache_mcp_globals()` extracts all MCP context once and stores it on the session
- AND no redundant extraction occurs during tool execution

## REMOVED Requirements

### Requirement: MCP Context Deduplication (old ContextVar-based)
**Reason**: Replaced by session-scoped storage above. `CachedMcpContext` and the
module-level `_cached_mcp_context` global are removed.
**Migration**: Read/write agent info via `session.agent_info` instead of
`get_cached_mcp_context()` / `set_cached_mcp_context()`.
