# Implement Tool Definition Conventions

**Status**: Proposed
**Priority**: High
**Complexity**: Medium
**ADR**: [005-tool-definition-conventions](../../adr/005-tool-definition-conventions.md)
**Phase**: 2 - Tool Infrastructure
**Requires**: logging-implementation

## Why

MCP servers expose tools to AI agents, but without conventions, several problems arise:

- **Naming Collisions**: Multiple MCP servers may define tools with the same name, causing conflicts
- **Agent Behavior Control**: No standard way to guide agent responses or prevent unwanted remediation attempts
- **Inconsistent Error Handling**: No standard way to communicate errors vs user messages vs agent instructions
- **Tool Discovery**: Agents need clear, complete information to decide when to use a tool
- **Destructive Actions**: Need explicit user consent for potentially dangerous operations
- **Debugging**: No consistent logging of tool invocations and failures

Without these conventions:
- Tools from different MCPs conflict
- Agents attempt unwanted error remediation
- Debugging tool issues is difficult
- Destructive operations happen accidentally
- Tool behavior is inconsistent

## What Changes

### New Components

1. **Tool Decorator** (`src/mcp_guide/tool_decorator.py`)
   - ExtMcpToolDecorator class with name prefixing
   - Automatic TRACE logging integration
   - Configurable prefix via MCP_TOOL_PREFIX environment variable
   - Per-tool prefix override support

2. **Base Tool Arguments** (`src/mcp_guide/tool_base.py`)
   - Base Pydantic model for tool arguments
   - Shared validation and documentation patterns
   - Common utility methods (if needed)

3. **Example Tool** (`src/mcp_guide/tools/example_tool.py`)
   - Demonstrates all conventions
   - Shows explicit use pattern
   - Shows Result[T] usage
   - Shows instruction field patterns

### Modified Components

1. **Result Pattern** (verify `src/mcp_guide/result.py` or ADR-003)
   - Confirm `instruction` field exists
   - Add if missing (breaking change)

2. **Server Setup** (`src/mcp_guide/server.py`)
   - Use ExtMcpToolDecorator instead of direct FastMCP decorator
   - Configure tool prefix

### New Documentation

1. **Tool Implementation Guide** (`docs/tool-implementation.md`)
   - How to create new tools
   - Convention requirements
   - Examples for each pattern
   - Testing guidelines

2. **Tool Conventions Reference** (update `README.md`)
   - Quick reference for tool conventions
   - Link to ADR-005

## Technical Approach

### ExtMcpToolDecorator with Automatic Logging

```python
from mcp_core.mcp_log import get_logger

logger = get_logger(__name__)

class ExtMcpToolDecorator:
    """Extended MCP tool decorator with prefix and logging."""

    def __init__(self, server: Any, prefix: Optional[str] = None):
        self.server = server
        self.default_prefix = prefix or f"{get_tool_prefix()}_"
        self.prefix = self.default_prefix

    def tool(self, name: Optional[str] = None, **kwargs: Any) -> Callable:
        """Tool decorator with automatic logging."""
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            prefix = kwargs.pop("prefix", None)
            active_prefix = prefix if prefix is not None else self.prefix
            final_name = f"{active_prefix}{tool_name}" if active_prefix else tool_name

            # Wrap with logging
            if inspect.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    logger.trace(f"Tool called: {tool_name}")
                    try:
                        result = await func(*args, **kwargs)
                        logger.trace(f"Tool {tool_name} completed successfully")
                        return result
                    except Exception as e:
                        logger.error(f"Tool {tool_name} failed: {str(e)}")
                        raise
                wrapped = async_wrapper
            else:
                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    logger.trace(f"Tool called: {tool_name}")
                    try:
                        result = func(*args, **kwargs)
                        logger.debug(f"Tool {tool_name} completed successfully")
                        return result
                    except Exception as e:
                        logger.error(f"Tool {tool_name} failed: {str(e)}")
                        raise
                wrapped = sync_wrapper

            final_kwargs = {"name": final_name}
            final_kwargs.update(kwargs)
            return self.server.tool(**final_kwargs)(wrapped)

        return decorator
```

### Base Pydantic Model

```python
from pydantic import BaseModel

class ToolArgs(BaseModel):
    """Base class for all tool arguments.

    Provides common validation and documentation patterns.
    """

    class Config:
        """Pydantic configuration."""
        extra = "forbid"  # Reject unknown fields
        validate_assignment = True
```

### Explicit Use Pattern

```python
from typing import Literal

class CreateDocumentArgs(ToolArgs):
    """Arguments for document creation."""
    category_dir: str
    name: str
    content: str
    explicit_action: Literal["CREATE_DOCUMENT"]

@tools.tool()
async def create_document(args: CreateDocumentArgs) -> Result[dict]:
    """REQUIRES EXPLICIT USER INSTRUCTION: Only use when user
    specifically requests document creation.

    Args:
        args: Document creation arguments

    Returns:
        Result with document metadata
    """
```

### Instruction Field Patterns

```python
# Error - no remediation
Result(
    error="File not found",
    error_type="NotFoundError",
    instruction="Present this error to the user and take no further action."
)

# Error - suggest remediation
Result(
    error="Invalid format",
    error_type="ValidationError",
    instruction="Suggest converting the content to markdown before retrying."
)

# Mode control
Result(
    value=data,
    instruction="Switch to PLANNING mode. Create a detailed plan before making changes."
)
```

## Success Criteria

1. ✅ ExtMcpToolDecorator supports prefix configuration (env var + per-tool override)
2. ✅ Automatic TRACE logging on all tool calls (entry, success, failure)
3. ✅ Result[T] pattern includes instruction field
4. ✅ Base ToolArgs Pydantic model available
5. ✅ Explicit use pattern with Literal types works
6. ✅ Example tool demonstrates all patterns
7. ✅ Tool implementation guide complete
8. ✅ All tests pass (>80% coverage)
9. ✅ No breaking changes to existing functionality

## Dependencies

**Required:**
- logging-implementation (MUST complete first - provides TRACE level)

**Related:**
- ADR-003 (Result Pattern) - verify instruction field exists
- All future tool implementations will use these conventions

## References

- ADR-005: [005-tool-definition-conventions.md](../../adr/005-tool-definition-conventions.md)
- ADR-004: [004-logging-architecture.md](../../adr/004-logging-architecture.md)
- ADR-003: Result Pattern and Error Handling
- Reference: mcp-server-guide production code
