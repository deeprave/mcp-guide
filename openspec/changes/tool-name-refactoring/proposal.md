# Change: Refactor Tool Names for Consistency

## Why

Current tool naming is inconsistent with unnecessary "get_" and "set_" prefixes. Simplifying names improves clarity and reduces verbosity for AI agents while maintaining clear intent.

## What Changes

Rename the following tools:
- `get_category_content` → `category_content`
- `get_collection_content` → `collection_content`
- `get_client_info` → `client_info`
- `get_current_project` → `get_project`
- `set_current_project` → `set_project`

Keep `get_content` as-is (may be revisited in future changes).

Update all:
- Tool registration code
- Tool implementation modules
- Tests
- Documentation
- OpenAPI specs

## Impact

- **Affected specs**: `tool-infrastructure`
- **Affected code**:
  - `src/mcp_guide/tools/tool_*.py` - Tool implementations
  - `src/mcp_guide/server.py` - Tool registration
  - `tests/` - All tool tests
  - Documentation references
- **Breaking change**: Yes - existing tool names will no longer work
- **Benefits**:
  - Consistent naming convention
  - Reduced verbosity
  - Clearer tool intent

## Acceptance Criteria

- [ ] All 5 tools renamed in implementation
- [ ] Tool registration updated
- [ ] All tests updated and passing
- [ ] Documentation updated
- [ ] Spec delta added to tool-infrastructure
- [ ] No references to old tool names remain
