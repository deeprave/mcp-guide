## 0. Pre-Migration (can be done independently)
- [ ] 0.1 Change `mcp[cli]>=1.16.0` to `mcp>=1.16.0` in pyproject.toml (drops unused `typer`, `python-dotenv`)
- [ ] 0.2 Run `uv lock` and verify no breakage

## 1. Investigation Spike
- [ ] 1.1 Install `fastmcp` in dev environment and verify import compatibility
- [ ] 1.2 Check `ExtMcpToolDecorator` compatibility with FastMCP 3.x
- [ ] 1.3 Identify any `mcp[cli]` CLI commands in use that need replacement

## 2. Dependency Update
- [ ] 2.1 Replace `mcp[cli]>=1.16.0` with `fastmcp>=3.1.0` in pyproject.toml
- [ ] 2.2 Remove any other direct `mcp` dependency if now transitive
- [ ] 2.3 Run `uv lock` and verify dependency resolution

## 3. Core Refactoring
- [ ] 3.1 Update `GuideMCP` in guide.py — change import, remove `set_instructions()` (dead code, also removes `_mcp_server` private access), remove `agent_info` attribute (shared mutable state bug — breaks multi-client HTTP)
- [ ] 3.2 Update `tool_utility.py` — remove `mcp.agent_info` cache read/write; read `agent_info` from `session.agent_info` directly (already populated by `mcp_context.py` bootstrap)
- [ ] 3.3 Update transports/stdio.py — change FastMCP import
- [ ] 3.4 Update server.py — change Context import and any constructor patterns

## 4. Import Updates
- [ ] 4.1 Update all `from mcp.server.fastmcp import Context` to `from fastmcp import Context` across tool files, prompts, resources, session, mcp_context, and core/tool_decorator

## 5. Verification
- [ ] 5.1 Run full test suite and fix any failures
- [ ] 5.2 Start server in stdio mode and verify tool registration
- [ ] 5.3 Start server in http mode and verify transport works
- [ ] 5.4 Verify prompts and resources still function correctly
