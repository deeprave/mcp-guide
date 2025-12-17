# Change: Tool Refactor for Internal Function Calls

## Why
Currently, MCP tools return strings directly, making them unsuitable for internal use by other system components (like prompts). This creates architectural problems:

- Prompts cannot safely call tool logic without bypassing MCP validation
- No way to get structured results from tools for internal processing
- Tools mix business logic with MCP string formatting
- Error handling is inconsistent between internal and external calls

## What Changes
Refactor all MCP tools to follow a two-layer pattern:

### Layer 1: Internal Functions
- Private functions (e.g., `_get_content`) that contain business logic
- Take an Arguments subclass as input
- Return `Result[T]` for structured error handling
- Can be safely called by other system components

### Layer 2: MCP Tool Wrappers
- Public MCP tool functions (e.g., `get_content`)
- Call internal function and handle Result
- Convert successful results to JSON string for MCP protocol
- Convert errors to appropriate string format

### Example Pattern
```python
# Internal function - returns structured Result
async def _get_content(args: ContentArgs, ctx: Optional[Context] = None) -> Result[ContentData]:
    # Business logic here
    if error_condition:
        return Result.error("Something went wrong")
    return Result.ok(content_data)

# MCP tool wrapper - returns string for protocol
@tools.tool(args_class=ContentArgs)
async def get_content(args: ContentArgs, ctx: Optional[Context] = None) -> str:
    result = await _get_content(args, ctx)
    if result.success:
        return result.data.to_json()  # or appropriate string conversion
    else:
        return f"Error: {result.error}"
```

## Impact
- **BREAKING**: Internal function signatures change (return Result instead of string)
- **NON-BREAKING**: MCP tool interfaces remain the same (still return strings)
- Enables safe internal tool usage by prompts and other components
- Improves error handling consistency
- Separates business logic from MCP protocol concerns

## Affected Tools
All existing tools need refactoring:
- `get_content` → `_get_content`
- `get_project` → `_get_project`
- `set_project` → `_set_project`
- All category, collection, utility tools
