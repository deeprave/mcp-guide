## 1. Core Infrastructure
- [ ] 1.1 Define standard Result data types for each tool category
- [ ] 1.2 Create conversion utilities for Result → JSON string
- [ ] 1.3 Establish naming convention for internal vs MCP functions

## 2. Content Tools Refactor
- [ ] 2.1 Refactor `get_content` → `_get_content` + wrapper
- [ ] 2.2 Define `ContentData` result type
- [ ] 2.3 Update guide prompt to use `_get_content`

## 3. Project Tools Refactor
- [ ] 3.1 Refactor `get_project` → `_get_project` + wrapper
- [ ] 3.2 Refactor `set_project` → `_set_project` + wrapper
- [ ] 3.3 Define project result types

## 4. Category Tools Refactor
- [ ] 4.1 Refactor category list tools
- [ ] 4.2 Refactor category management tools
- [ ] 4.3 Define category result types

## 5. Collection Tools Refactor
- [ ] 5.1 Refactor collection list tools
- [ ] 5.2 Refactor collection management tools
- [ ] 5.3 Define collection result types

## 6. Utility Tools Refactor
- [ ] 6.1 Refactor utility tools
- [ ] 6.2 Define utility result types

## 7. Testing & Validation
- [ ] 7.1 Update all tool tests to test both internal and MCP functions
- [ ] 7.2 Add integration tests for internal function usage
- [ ] 7.3 Verify MCP protocol compliance unchanged

## Implementation Notes

**Naming Convention:**
- Internal functions: `_function_name` (private, returns Result)
- MCP tools: `function_name` (public, returns string)

**Result Types:**
- Each tool category should have appropriate data classes
- Use `Result[DataClass]` for structured returns
- Consistent error message formatting

**Conversion Pattern:**
```python
async def mcp_tool(args: Args, ctx: Context) -> str:
    result = await _internal_function(args, ctx)
    return result.data.to_json() if result.success else f"Error: {result.error}"
```
