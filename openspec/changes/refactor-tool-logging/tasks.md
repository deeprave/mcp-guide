# Implementation Tasks

## Phase 1: Create Helper Infrastructure
- [ ] Create `src/mcp_guide/tools/tool_result.py` with `_tool_result()` function
  - [ ] Import Result, TaskManager, logger
  - [ ] Accept `tool_name: str` and `result: Result[T]` parameters
  - [ ] Call `task_manager.process_result(result)` if `task_manager` is available
  - [ ] Log result at TRACE level with result.to_json()
  - [ ] Return `result.to_json_str()`
  - [ ] Add comprehensive docstring
- [ ] Export `_tool_result` from `src/mcp_guide/tools/__init__.py`
- [ ] Write unit tests for `_tool_result()` function
  - [ ] Test with TaskManager available
  - [ ] Test with TaskManager unavailable
  - [ ] Test logging output
  - [ ] Test JSON string return

## Phase 2: Update Tool Decorator
- [ ] Remove `_log_tool_result()` function from `src/mcp_guide/core/tool_decorator.py`
- [ ] Remove `_process_tool_result()` function (except `on_tool()` call)
- [ ] Simplify decorator to only call `on_tool()` at start
- [ ] Update decorator to return tool result directly (no processing)
- [ ] Update decorator tests to reflect simplified behavior

## Phase 3: Update Tools (Systematic Migration)
- [ ] Update `tool_project.py` - 5 tools
  - [ ] Import `_tool_result`
  - [ ] Replace `return result.to_json_str()` with `return _tool_result("tool_name", result)`
- [ ] Update `tool_category.py` - 7 tools
- [ ] Update `tool_collection.py` - 5 tools
- [ ] Update `tool_feature_flags.py` - 6 tools
- [ ] Update `tool_content.py` - 1 tool
- [ ] Update `tool_filesystem.py` - 4 tools
- [ ] Update `tool_utility.py` - 1 tool
- [ ] Update any other tool files discovered

## Phase 4: Testing & Validation
- [ ] Run full test suite - all tests must pass
- [ ] Verify TRACE logging appears in logs for tool results
- [ ] Verify TaskManager result processing works correctly
- [ ] Run quality checks (ruff, mypy, formatting)
- [ ] Manual testing: invoke tools and check logs

## Phase 5: Documentation
- [ ] Update tool-infrastructure spec with new pattern
- [ ] Update tool README if it references result handling
- [ ] Add comments explaining the pattern in tool_result.py

## Notes
- Total tools to update: ~29 return statements across 7 files
- Pattern is consistent: `return _tool_result("tool_name", result)`
- Tool name should match the actual tool function name (without prefix)
- Keep `on_tool()` call in decorator - it's separate from result processing
