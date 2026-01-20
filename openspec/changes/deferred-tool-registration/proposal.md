# Change: Deferred Tool Registration Pattern

## Why

Current tool registration uses decorators that execute on module import, causing:
- Test contamination from Python's module caching
- Complex `mcp_server_factory` fixture workarounds
- Tight coupling between import and registration
- Fragile tests that fail in full suite due to import order

## What Changes

Replace import-time `@tools.tool()` decorators with deferred registration:
- Add `@toolfunc()` decorator that stores metadata without MCP registration
- Add `register_tools(mcp)` function for explicit registration during server init
- Remove `mcp_server_factory` fixture workaround
- Update all 8 tool modules to use new pattern

## Impact

- Affected specs: `tool-registration` (new capability)
- Affected code:
  - `src/mcp_guide/tools/tool_*.py` (8 modules)
  - `tests/integration/conftest.py` (remove workaround)
  - `src/mcp_guide/core/tool_decorator.py` (new decorator)
  - `src/mcp_guide/server.py` (add explicit registration)
