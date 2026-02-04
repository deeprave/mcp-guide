# Change: Refactor Tool Result Logging and Processing

## Why
FastMCP requires tools to return `str` (JSON strings), not `Result[T]` objects. The current architecture attempts to log and process results in the tool decorator (`ExtMcpToolDecorator`), but this fails because:

1. Tools return `result.to_json_str()` (a string), not `Result` objects
2. The decorator's `isinstance(result, Result)` check is always False
3. Result logging never executes (TRACE logs never appear)
4. TaskManager result processing happens in decorator but can't access the Result object

This creates a disconnect between the Result pattern and the actual tool execution flow.

## What Changes
- Create `_tool_result(tool_name: str, result: Result[T]) -> str` helper function
- Move result logging into the helper (before JSON conversion)
- Move TaskManager `process_result()` into the helper (before JSON conversion)
- Update all tools to use `return _tool_result("tool_name", result)` instead of `return result.to_json_str()`
- Remove result logging and processing logic from `ExtMcpToolDecorator`
- Keep `on_tool()` call in decorator (happens at tool start, not result processing)

## Impact
- Affected specs: `tool-infrastructure`
- Affected code:
  - `src/mcp_guide/core/tool_decorator.py` - Remove result processing, keep on_tool()
  - `src/mcp_guide/tools/tool_result.py` - New helper function
  - All tool files in `src/mcp_guide/tools/` - Update return statements
  - Tests for tool decorator and individual tools

## Benefits
- Result logging actually works (logs appear at TRACE level)
- TaskManager can process Result objects before JSON conversion
- Clearer separation: decorator handles invocation, helper handles results
- Consistent pattern across all tools
- Easier to debug tool execution flow

## Migration Path
1. Create `_tool_result()` helper with logging and processing
2. Update one tool as proof of concept
3. Update remaining tools systematically
4. Remove dead code from decorator
5. Update tests

## Related Issues
This change addresses the tool result logging issue. There is a separate unresolved issue with instruction queue delivery during server initialization:
- WorkflowMonitorTask queues instructions during `on_init()`
- Instructions are confirmed queued in logs
- Instructions never appear in `additional_agent_instructions`
- Likely issue: instruction queue delivery mechanism doesn't handle startup-queued instructions
- Needs separate investigation of `queue_instruction()` and how instructions attach to responses
