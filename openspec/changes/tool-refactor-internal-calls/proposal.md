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
- Functions prefixed with `internal_` (e.g., `internal_get_content`) that contain business logic
- Take an Arguments subclass as input
- Return `Result[T]` for structured error handling
- Can be safely called by other system components
- Exported via `__all__` for explicit cross-module access

### Layer 2: MCP Tool Wrappers
- Public MCP tool functions (e.g., `get_content`)
- Call internal function and handle Result
- Convert results to JSON string using `Result.to_json_str()`
- NOT exported in `__all__` - decorator handles MCP registration

## Impact
- **BREAKING**: Internal function signatures change (return Result instead of string)
- **NON-BREAKING**: MCP tool interfaces remain the same (still return strings)
- Enables safe internal tool usage by prompts and other components
- Improves error handling consistency
- Separates business logic from MCP protocol concerns
- Clear API surface via explicit exports

## Affected Tools
All existing tools need refactoring:
- `get_content` → `internal_get_content`
- `get_project` → `internal_get_project`
- `set_project` → `internal_set_project`
- All category, collection, utility tools
