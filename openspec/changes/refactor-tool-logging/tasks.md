# Implementation Tasks

## Phase 1: Create Helper Infrastructure
- [x] Create `src/mcp_guide/tools/tool_result.py` with `tool_result()` function
  - [x] Import Result, TaskManager, logger
  - [x] Accept `tool_name: str` and `result: Result[T]` parameters
  - [x] Call `task_manager.process_result(result)` if `task_manager` is available
  - [x] Log result at TRACE level with result.to_json()
  - [x] Return `result.to_json_str()`
  - [x] Add comprehensive docstring
- [x] Export `tool_result` from `src/mcp_guide/tools/__init__.py`
- [x] Write unit tests for `tool_result()` function
  - [x] Test with TaskManager available
  - [x] Test with TaskManager unavailable
  - [x] Test logging output
  - [x] Test JSON string return

## Phase 2: Update Tool Decorator
- [x] Remove `_log_tool_result()` function from `src/mcp_guide/core/tool_decorator.py`
- [x] Remove `_process_tool_result()` function (except `on_tool()` call)
- [x] Simplify decorator to only call `on_tool()` at start
- [x] Update decorator to return tool result directly (no processing)
- [x] Update decorator tests to reflect simplified behavior

## Phase 3: Update Tools (Systematic Migration)
- [x] Update `tool_filesystem.py` - 4 tools
  - [x] Import `tool_result`
  - [x] Replace `return result.to_json_str()` with `return tool_result("tool_name", result)`
- [x] Update `tool_category.py` - 3 tools
- [x] Update `tool_collection.py` - 5 tools

## Phase 4: Testing & Validation
- [x] Run full test suite - all tests must pass (1273 passed)
- [x] Verify TRACE logging appears in logs for tool results
- [x] Verify TaskManager result processing works correctly
- [x] Run quality checks (ruff, mypy, formatting) - all passed
- [ ] Manual testing: invoke tools and check logs

## Phase 5: Documentation
- [ ] Update tool-infrastructure spec with new pattern
- [ ] Update tool README if it references result handling
- [ ] Add comments explaining the pattern in tool_result.py

## Summary
Implementation complete. All automated tests and quality checks pass.

**Completed:**
- Created `tool_result()` helper function with logging and TaskManager processing
- Simplified tool decorator to only call `on_tool()` at start
- Updated 12 tool return statements across 3 files (tool_filesystem, tool_category, tool_collection)
- All 1273 tests passing
- All quality checks passing (ruff, mypy, formatting)

**Remaining:**
- Manual testing to verify TRACE logs appear
- Documentation updates
