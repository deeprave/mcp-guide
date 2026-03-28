# Fix prompt arguments not received in TUI mode

**Status**: Proposed
**Priority**: High
**Complexity**: Low

## Why

- The `guide` prompt's arguments are not being received when invoked from TUI mode (e.g. Kiro CLI), though they work correctly in stdio mode
- This may be caused by the `ToolArguments` (Pydantic `Arguments`) wrapper used elsewhere influencing how FastMCP registers prompt parameters, or by a mismatch between how TUI clients pass prompt arguments and how the explicit `arg1..argf` parameters are declared
- The prompt currently uses 15 explicit `Optional[str]` parameters as a workaround for MCP not supporting `*args` — this is fragile and may interact poorly with certain client implementations

## What Changes

- Investigate whether the `promptfunc` decorator or FastMCP prompt registration is dropping or misrouting arguments in TUI mode
- Determine if switching to plain function arguments (without the `promptfunc` decorator indirection) resolves the issue
- Simplify the argument passing if a cleaner approach is viable
