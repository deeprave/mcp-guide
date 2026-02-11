# Change: Add MCP Discovery

## Why

Discovery capabilities enable agents to enumerate available MCP capabilities (tools, prompts, resources) for introspection and self-awareness. Current tool registration uses decorators that execute on module import, causing test contamination and tight coupling.

## What Changes

- Implement deferred registration pattern with `@toolfunc()`, `@promptfunc()`, `@resourcefunc()` decorators
- Add `register_tools()`, `register_prompts()`, `register_resources()` functions for explicit registration
- Implement `list_tools` tool (enumerate available tools)
- Implement `list_prompts` tool (enumerate available prompts)
- Implement `list_resources` tool (enumerate available resources)
- Return Result pattern responses
- Follow tool conventions (ADR-008)
- Remove test workarounds for import-time registration

## Impact

- Affected specs:
  - New capability `mcp-discovery` (tools, prompts, resources)
  - New capability `tool-registration` (deferred registration pattern)
- Affected code:
  - All tool modules (8 modules) - convert to `@toolfunc()`
  - New discovery tools module
  - `src/mcp_guide/core/tool_decorator.py` (new decorators and registry)
  - `src/mcp_guide/server.py` (explicit registration)
  - `tests/integration/conftest.py` (remove workarounds)
- Dependencies: Result pattern (ADR-003), tool conventions (ADR-008)
- Breaking changes: None (internal refactor + new tools)
