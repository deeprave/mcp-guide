## 0. Pre-Migration
- [x] 0.1 Change `mcp[cli]>=1.16.0` to `mcp>=1.16.0` in pyproject.toml (already done)
- [x] 0.2 Run `uv lock` and verify no breakage (already done — uv.lock has `mcp = "1.26.0"` with no cli extras)

## 1. Investigation Spike
- [x] 1.1 Install `fastmcp` in dev environment and verify import compatibility
- [x] 1.2 Check `ExtMcpToolDecorator` compatibility with FastMCP 3.x (`mcp.tool(name=..., description=...)` API)
- [x] 1.3 Verify `GuideMCP` constructor kwargs (`instructions=`, `lifespan=`) still valid in FastMCP 3.x
- [x] 1.4 Verify `ctx.fastmcp`, `ctx.session`, `ctx.session.client_params` still available on `Context` in FastMCP 3.x
- [x] 1.5 Verify `run_stdio_async()` still exists on FastMCP instance
- [x] 1.6 Identify any `mcp[cli]` CLI commands in use that need replacement

## 2. Dependency Update
- [x] 2.1 Replace `mcp>=1.16.0` with `fastmcp>=3.1.0` in pyproject.toml
- [x] 2.2 Remove any other direct `mcp` dependency if now transitive
- [x] 2.3 Run `uv lock` and verify dependency resolution

## 3. Core Refactoring
- [x] 3.1 Update `GuideMCP` in guide.py — change import to `from fastmcp import FastMCP`, remove `set_instructions()` (dead code, removes `_mcp_server` private access), remove `agent_info` attribute (shared mutable state bug — breaks multi-client HTTP)
- [x] 3.2 Update `tool_utility.py` — remove `mcp.agent_info` cache read/write; read `agent_info` from `session.agent_info` directly (already populated by `mcp_context.py` bootstrap)
- [x] 3.3 Update `transports/stdio.py` — change import to `from fastmcp import FastMCP`
- [x] 3.4 Update `server.py` — change `Context` import to `from fastmcp import Context`

## 4. Import Updates
- [x] 4.1 Update all `from mcp.server.fastmcp import Context` to `from fastmcp import Context` across tool files, prompts, resources, session, mcp_context, and core/tool_decorator (19 import sites across 17 files)

## 5. Verification
- [x] 5.1 Run full test suite — 1674 passed, 0 failed
- [x] 5.2 ruff check — all checks passed
- [x] 5.3 ty check — all checks passed
- [ ] 5.4 Start server in stdio mode and verify tool registration
- [ ] 5.5 Start server in http mode and verify transport works
- [ ] 5.6 Verify prompts and resources still function correctly

## Additional fixes during implementation
- [x] Fix `Context[Any, Any, Any]` generic usage in resources.py (FastMCP 3.x Context is not generic)
- [x] Update integration tests: replace `create_connected_server_and_client_session` with `Client(FastMCPTransport(...))` across 6 files
- [x] Fix `result.isError` → `result.is_error` in test_tool_project.py (FastMCP 3.x snake_case)
- [x] Fix pre-existing bug in test_clone_with_conflicts: `category_add` was never a registered tool, replaced with `category_collection_add`
- [x] Fix `tests/test_server.py` importing `FastMCP` from old `mcp.server` location
- [x] Update `test_tool_utility.py` to test session-based agent_info (not GuideMCP cache)
- [x] Fix `client_params` type: normalise `InitializeRequestParams` → `dict` via `model_dump()` before storing on session
