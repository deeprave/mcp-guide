## Context
The project currently depends on `mcp[cli]>=1.16.0` which vendors FastMCP 1.0 at `mcp.server.fastmcp`. This vendored copy is effectively frozen — the standalone `fastmcp` package (PrefectHQ) has evolved to v3.x with active maintenance, better APIs, and additional capabilities. Continuing to use the vendored copy means missing fixes, accumulating technical debt, and relying on a stale API surface.

## Goals / Non-Goals
- Goals: Replace vendored FastMCP with standalone package, eliminate private attribute access, align with current FastMCP APIs
- Non-Goals: Adopt FastMCP-specific features (composition, middleware, apps, clients) — those are future work

## Decisions
- Decision: Depend on `fastmcp>=3.1.0` and remove `mcp[cli]` from direct dependencies
  - FastMCP includes `mcp>=1.24.0,<2.0` as a transitive dependency, so low-level `mcp.*` imports still work
  - The `[cli]` extra is already unused — we don't import `typer` or `python-dotenv` anywhere, and we have our own entry points (`mcp-guide`, `mcp-install`)

- Decision: Fix `GuideMCP.set_instructions()` to use FastMCP 3.x public API
  - Current code accesses `self._mcp_server.instructions` (private attribute — violates INSTRUCTIONS.md rule #9)
  - FastMCP 3.x `FastMCP` constructor accepts `instructions` parameter directly
  - Alternatively, check if FastMCP 3.x exposes a public setter or property

- Decision: Keep `GuideMCP` as a `FastMCP` subclass for now
  - Minimises migration scope
  - Composition can be explored in a future change

## Dependency Analysis

### Current: `mcp[cli]>=1.16.0` (v1.26.0 installed)
- Core `mcp` deps: anyio, httpx, httpx-sse, jsonschema, pydantic, pydantic-settings, pyjwt, python-multipart, sse-starlette, starlette, typing-extensions, typing-inspection, uvicorn
- `[cli]` extra adds: `typer`, `python-dotenv` — **neither is used by our code**

### Proposed: `fastmcp>=3.1.0`
Core direct dependencies (only 6):
- `python-dotenv>=1.1.0`
- `exceptiongroup>=1.2.2`
- `httpx>=0.28.1,<1.0`
- `mcp>=1.24.0,<2.0` (transitive — keeps entire existing mcp tree)
- `openapi-pydantic>=0.0`
- `watchfiles>=1.0.0`

Optional extras (not needed): `anthropic`, `apps`, `azure`, `code-mode`, `gemini`, `openai`, `tasks`

### Net dependency changes
| Action | Packages |
|--------|----------|
| Dropped (from `mcp[cli]`) | `typer` |
| New direct | `exceptiongroup`, `openapi-pydantic`, `watchfiles` |
| Returned | `python-dotenv` (dropped from `[cli]`, gained from fastmcp core) |
| New transitive | ~26 packages (jsonref, jsonschema-path, pathable, websockets, etc.) |

The core is lean. Many transitive packages are small utilities. No "lite" install option exists, but the optional extras (AI SDK integrations) are not required.

### Pre-migration quick win
The `[cli]` extra can be dropped independently — changing `mcp[cli]>=1.16.0` to `mcp>=1.16.0` removes `typer` and `python-dotenv` with zero code changes.

## Risks / Trade-offs
- FastMCP 3.x decorator behaviour change (returns original function, not FunctionTool) — low risk since mcp-guide uses its own `ExtMcpToolDecorator`
- Transitive dependency tree grows (~26 new packages) — acceptable for an actively maintained framework; core deps are minimal
- FastMCP 3.x may have subtle behavioural differences in transport handling — mitigated by thorough testing

## Open Questions
- Does FastMCP 3.x expose a public API for setting instructions post-construction, or must they be set at construction time?
- Does the `ExtMcpToolDecorator` need changes for FastMCP 3.x compatibility?
