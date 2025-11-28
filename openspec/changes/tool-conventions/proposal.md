# Implement Tool Definition Conventions

**Status**: Proposed
**Priority**: High
**Complexity**: Medium
**ADR**: [008-tool-definition-conventions](../../adr/008-tool-definition-conventions.md)
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

### New Components (mcp_core - generic, reusable)

1. **Result Pattern** (`src/mcp_core/result.py`) - JIRA: GUIDE-23
   - Generic Result[T] dataclass for tool responses
   - Fields: success, value, error, error_type, exception, message, instruction
   - Helper methods: ok(), failure(), is_ok(), is_failure(), to_json(), to_json_str()
   - JSON serialization for MCP responses

2. **Tool Arguments Base** (`src/mcp_core/tool_arguments.py`) - JIRA: GUIDE-10
   - Base Pydantic model with common validation (extra="forbid", validate_assignment=True)
   - Tool collection pattern with @ToolArguments.declare decorator
   - get_declared_tools() method with asyncio lock for thread safety
   - to_schema_markdown() for generating markdown-formatted schemas
   - build_tool_description() for combining docstrings with schemas

3. **Tool Decorator** (`src/mcp_core/tool_decorator.py`) - JIRA: GUIDE-10
   - ExtMcpToolDecorator class with name prefixing
   - Automatic TRACE/DEBUG/ERROR logging integration
   - Reads MCP_TOOL_PREFIX environment variable (no hardcoded default)
   - Per-tool prefix override support

### Modified Components (mcp_guide - project-specific)

1. **Environment Configuration** (`src/mcp_guide/main.py`)
   - Add _configure_environment() function
   - Set MCP_TOOL_PREFIX="guide" if not already set
   - Call before _configure_logging() and server initialization

2. **Server Setup** (`src/mcp_guide/server.py`)
   - Use ExtMcpToolDecorator instead of direct FastMCP decorator
   - Import tool modules (triggers @ToolArguments.declare collection)
   - Call get_declared_tools() to retrieve collected tools
   - Generate descriptions with build_tool_description()
   - Register tools with generated descriptions
   - Conditional import of tool_example based on MCP_INCLUDE_EXAMPLE_TOOLS

3. **Example Tool** (`src/mcp_guide/tools/tool_example.py`)
   - Demonstrates all conventions (temporary, conditionally included)
   - Shows @ToolArguments.declare pattern
   - Shows explicit use pattern with Literal types
   - Shows Result[T] usage with instruction field
   - Can be excluded by not setting MCP_INCLUDE_EXAMPLE_TOOLS=true

### New Documentation

1. **Tool Implementation Guide** (`docs/tool-implementation.md`)
   - How to create new tools
   - Convention requirements
   - Examples for each pattern
   - Testing guidelines

2. **Tool Conventions Reference** (update `README.md`)
   - Quick reference for tool conventions
   - Environment variables (MCP_TOOL_PREFIX, MCP_INCLUDE_EXAMPLE_TOOLS)
   - Link to ADR-008

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

1. ✅ Result[T] pattern implemented in mcp_core with instruction field (GUIDE-23)
2. ✅ ToolArguments base class in mcp_core with collection pattern (GUIDE-10)
3. ✅ @ToolArguments.declare decorator for tool collection
4. ✅ get_declared_tools() with asyncio lock for thread safety
5. ✅ to_schema_markdown() generates markdown-formatted schemas
6. ✅ build_tool_description() combines docstrings with schemas
7. ✅ ExtMcpToolDecorator in mcp_core with no hardcoded default prefix
8. ✅ Automatic TRACE/DEBUG/ERROR logging on all tool calls
9. ✅ MCP_TOOL_PREFIX environment variable support
10. ✅ _configure_environment() sets default prefix early in startup
11. ✅ Server integration uses collection pattern for automatic registration
12. ✅ Example tool demonstrates all patterns (conditionally included)
13. ✅ Tool implementation guide complete
14. ✅ All tests pass (>80% coverage)
15. ✅ No breaking changes to existing functionality

## Dependencies

**Required:**
- logging-implementation (MUST complete first - provides TRACE level)

**Related:**
- ADR-003 (Result Pattern) - verify instruction field exists
- All future tool implementations will use these conventions

## References

- ADR-008: [008-tool-definition-conventions.md](../../adr/008-tool-definition-conventions.md)
- ADR-004: [004-logging-architecture.md](../../adr/004-logging-architecture.md)
- ADR-003: Result Pattern for Tool and Prompt Responses
- Reference: mcp-server-guide production code
