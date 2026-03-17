# Change: Migrate from vendored FastMCP to standalone FastMCP package

## Why
The project currently depends on `mcp[cli]` which vendors FastMCP 1.0 at `mcp.server.fastmcp`. This vendored copy is effectively frozen — the standalone `fastmcp` package (by PrefectHQ) has evolved to v3.x with active maintenance, better APIs, and additional capabilities. Continuing to use the vendored copy means missing fixes, accumulating technical debt, and relying on a stale API surface.

## What Changes
- Replace `mcp[cli]` dependency with `fastmcp` (which includes `mcp` transitively)
- Update all imports from `mcp.server.fastmcp` / `mcp.server` to `fastmcp`
- Refactor `GuideMCP` subclass to use public FastMCP 3.x APIs (eliminates existing private attribute access to `_mcp_server.instructions`)
- Update transport handling to align with FastMCP 3.x patterns
- Update any prompt functions if they return `mcp.types.PromptMessage` objects

## Impact
- Affected specs: mcp-server, http-transport
- Affected code: guide.py, server.py, transports/, all tool files (Context import), prompts/
- 19 import sites across 17 files need updating
- `GuideMCP.set_instructions()` must stop accessing private `_mcp_server` attribute
- No user-facing behavioral changes expected

## Pre-Migration Quick Win
The `[cli]` extra on `mcp` is already unused — we don't import `typer` or `python-dotenv` anywhere. Changing `mcp[cli]>=1.16.0` to `mcp>=1.16.0` in pyproject.toml can be done immediately with zero code changes, dropping dead dependencies before the full migration.
