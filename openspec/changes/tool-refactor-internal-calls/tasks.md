## 1. Core Infrastructure
- [ ] 1.1 Define standard Result data types for each tool category
- [ ] 1.2 Create conversion utilities for Result → JSON string (if needed beyond to_json_str())
- [ ] 1.3 Establish naming convention: `internal_*` for internal functions, `__all__` exports

## 2. Content Tools Refactor
- [ ] 2.1 Refactor `get_content` → `internal_get_content` + wrapper
- [ ] 2.2 Define `ContentData` result type
- [ ] 2.3 Update guide prompt to use `internal_get_content`
- [ ] 2.4 Export `internal_get_content` via `__all__`

## 3. Project Tools Refactor
- [ ] 3.1 Refactor `get_project` → `internal_get_project` + wrapper
- [ ] 3.2 Refactor `set_project` → `internal_set_project` + wrapper
- [ ] 3.3 Define project result types
- [ ] 3.4 Export internal functions via `__all__`

## 4. Category Tools Refactor
- [ ] 4.1 Refactor category list tools → `internal_*` + wrappers
- [ ] 4.2 Refactor category management tools → `internal_*` + wrappers
- [ ] 4.3 Define category result types
- [ ] 4.4 Export internal functions via `__all__`

## 5. Collection Tools Refactor
- [ ] 5.1 Refactor collection list tools → `internal_*` + wrappers
- [ ] 5.2 Refactor collection management tools → `internal_*` + wrappers
- [ ] 5.3 Define collection result types
- [ ] 5.4 Export internal functions via `__all__`

## 6. Utility Tools Refactor
- [ ] 6.1 Refactor utility tools → `internal_*` + wrappers
- [ ] 6.2 Define utility result types
- [ ] 6.3 Export internal functions via `__all__`

## 7. Testing & Validation
- [ ] 7.1 Update all tool tests to test both internal and MCP functions
- [ ] 7.2 Add integration tests for internal function usage
- [ ] 7.3 Verify MCP protocol compliance unchanged
- [ ] 7.4 Update cross-module imports to use `internal_*` functions

## Implementation Notes

**Naming Convention:**
- Internal functions: `internal_function_name` (exported, returns Result)
- MCP tools: `function_name` (not exported, returns string)

**Module Exports:**
- Export internal functions via `__all__` for cross-module access
- Do NOT export MCP tools - decorator handles registration automatically

**Result Types:**
- Each tool category should have appropriate data classes
- Use `Result[DataClass]` for structured returns
- Consistent error message formatting via `Result.to_json_str()`

**Conversion Pattern:**
```python
async def mcp_tool(args: Args, ctx: Context) -> str:
    return await internal_function(args, ctx).to_json_str()

# Module exports
__all__ = ["internal_function"]
```

**Cross-Module Usage:**
```python
from mcp_guide.tools.tool_content import internal_get_content

# Use internal function directly
result = await internal_get_content(args, ctx)
if result.success:
    data = result.data  # Structured access
```
