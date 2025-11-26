# ADR-005: MCP Tool Definition Conventions

**Date:** 2025-11-27
**Status:** Accepted
**Dependencies:** ADR-004 (Logging Architecture), ADR-003 (Result Pattern)

## Context

MCP servers expose tools to AI agents, but without conventions, several problems arise:

1. **Naming Collisions**: Multiple MCP servers may define tools with the same name
2. **Agent Behavior Control**: Need to guide agent responses and prevent unwanted remediation attempts
3. **Inconsistent Error Handling**: No standard way to communicate errors vs user messages vs agent instructions
4. **Tool Discovery**: Agents need clear, complete information to decide when to use a tool
5. **Destructive Actions**: Need explicit user consent for potentially dangerous operations

This ADR establishes conventions for tool definition, naming, descriptions, and response handling in mcp-guide.

## Decision

### 1. Tool Name Decoration

All MCP tools MUST use a custom decorator that adds an optional prefix to tool names:

```python
class ExtMcpToolDecorator:
    """Extended MCP tool decorator with prefix handling."""

    def __init__(self, server: Any, prefix: Optional[str] = None):
        self.server = server
        self.default_prefix = prefix or f"{get_tool_prefix()}_"
        self.prefix = self.default_prefix

    def tool(self, name: Optional[str] = None, **kwargs: Any) -> Callable:
        """Tool decorator that handles prefix addition."""
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            prefix = kwargs.pop("prefix", None)
            active_prefix = prefix if prefix is not None else self.prefix
            final_name = f"{active_prefix}{tool_name}" if active_prefix else tool_name

            final_kwargs = {"name": final_name}
            final_kwargs.update(kwargs)

            return self.server.tool(**final_kwargs)(func)
        return decorator
```

**Prefix Configuration:**
- Default prefix from `MCP_TOOL_PREFIX` environment variable (default: "guide")
- Per-tool override via `prefix` kwarg in decorator
- Empty string disables prefix (for agents that auto-prefix)

**Documentation Convention:**
- All documentation, code, specifications, and references MUST use the **undecorated** tool name
- Prefix is an implementation detail for runtime collision avoidance

### 2. Tool Logging

All tool calls MUST be logged for debugging and audit purposes:

```python
def log_tool_usage(func: Callable) -> Callable:
    """Decorator to log tool usage."""
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tool_name = func.__name__
            logger.trace(f"Tool called: {tool_name}")
            try:
                result = await func(*args, **kwargs)
                logger.trace(f"Tool {tool_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {str(e)}")
                raise
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tool_name = func.__name__
            logger.trace(f"Tool called: {tool_name}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Tool {tool_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {str(e)}")
                raise
        return sync_wrapper
```

**Logging Levels:**
- TRACE: Tool invocation and successful completion (async)
- DEBUG: Successful completion (sync)
- ERROR: Tool failures with exception details

### 3. Tool Descriptions

Tool descriptions MUST be:
- **Succinct**: Brief, clear statement of purpose
- **Complete**: Include argument schema and usage patterns
- **Explicit**: Mark tools requiring explicit user consent

**Auto-Generated Schema:**
Tool descriptions SHOULD include auto-generated argument schema from Pydantic models:

```python
@mcp.tool()
async def create_document(
    category_dir: str,
    name: str,
    content: str,
    explicit_action: Literal["CREATE_DOCUMENT"]
) -> Result[dict]:
    """REQUIRES EXPLICIT USER INSTRUCTION: Only use when user specifically
    requests document creation or upload.

    This operation will create a new managed document in the specified category.
    Do not use frivolously or without clear user intent.

    Args:
        category_dir: Category directory path
        name: Document name
        content: Document content
        explicit_action: Must be 'CREATE_DOCUMENT' to confirm intentional creation

    Returns:
        Result with document metadata on success
    """
```

**Explicit Use Pattern:**
For destructive or significant operations, use `Literal` type hints to require exact string match:
- `explicit_action: Literal["CREATE_DOCUMENT"]`
- `explicit_action: Literal["DELETE_DOCUMENT"]`
- `explicit_action: Literal["UPDATE_DOCUMENT"]`

This prevents accidental invocation and ensures user intent.

### 4. Result Pattern

All tools MUST return `Result[T]` where T is JSON-serializable:

```python
@dataclass
class Result(Generic[T]):
    """Standard tool response."""
    # Success
    value: Optional[T] = None

    # Failure
    error: Optional[str] = None
    error_type: Optional[str] = None
    exception: Optional[str] = None

    # Both
    message: Optional[str] = None      # For user
    instruction: Optional[str] = None  # For agent
```

**Field Semantics:**

**Success Response:**
- `value`: Result data (optional - some tools just indicate success)
- `message`: Information for the user
- `instruction`: Guidance for the agent

**Failure Response:**
- `error`: What went wrong (required)
- `error_type`: Classification of error (required)
- `exception`: Exception details if applicable
- `message`: User-facing error explanation
- `instruction`: How agent should handle the error

**JSON-Serializable Types:**
T must be one of:
- Primitive types: `str`, `int`, `float`, `bool`, `None`
- Collections: `list`, `dict`, `tuple`
- Types with `.to_dict()` or `.to_json()` methods
- Pydantic models (auto-serializable)

### 5. Instruction Field Semantics

The `instruction` field controls agent behavior on receiving the response:

**Common Instruction Patterns:**

```python
# Error handling - prevent remediation
Result(
    error="File not found",
    error_type="NotFoundError",
    message="The requested file does not exist.",
    instruction="Present this error to the user and take no further action. "
                "Do not attempt to create the file or suggest alternatives."
)

# Error handling - suggest remediation
Result(
    error="Invalid format",
    error_type="ValidationError",
    message="The document format is invalid.",
    instruction="The document must be in markdown format. "
                "Suggest converting the content to markdown before retrying."
)

# Mode switching
Result(
    value={"status": "planning_required"},
    message="This operation requires planning.",
    instruction="Switch to PLANNING mode. Create a detailed plan before "
                "making any changes to the project."
)

# Operational boundaries
Result(
    value={"config": config_data},
    message="Configuration loaded successfully.",
    instruction="You are now in DISCUSSION mode. Gather requirements and "
                "create specifications. Do NOT make any changes to the project."
)
```

**Standard Instruction Vocabulary:**

While instructions are free-form text, these patterns are recommended:

**Error Handling:**
- `"Present this error to the user and take no further action."`
- `"Suggest [specific remediation] before retrying."`
- `"Ask the user for clarification on [specific aspect]."`

**Mode Control:**
- `"Switch to PLANNING mode."`
- `"Switch to DISCUSSION mode."`
- `"You are now in IMPLEMENTATION mode."`
- `"Return to CHECK mode."`

**Operational Boundaries:**
- `"Do NOT make any changes to the project."`
- `"Do NOT attempt to fix this automatically."`
- `"Require explicit user consent before proceeding."`
- `"This operation requires user review and approval."`

**Guidance:**
- `"Consider [alternative approach]."`
- `"Review [specific documentation] before proceeding."`
- `"Validate [specific aspect] with the user."`

### 6. Pydantic Validation

Tools SHOULD use Pydantic models for argument validation:

```python
from pydantic import BaseModel, Field

class CreateDocumentArgs(BaseModel):
    """Arguments for document creation."""
    category_dir: str = Field(..., description="Category directory path")
    name: str = Field(..., min_length=1, max_length=100, description="Document name")
    content: str = Field(..., description="Document content")
    explicit_action: Literal["CREATE_DOCUMENT"] = Field(
        ...,
        description="Must be 'CREATE_DOCUMENT' to confirm intent"
    )

@mcp.tool()
async def create_document(args: CreateDocumentArgs) -> Result[dict]:
    """Create a new document."""
    # Validation happens automatically
    # Access via args.category_dir, args.name, etc.
```

## Consequences

### Positive

- **Collision Avoidance**: Prefix prevents tool name conflicts across MCPs
- **Clear Communication**: Separate channels for user messages vs agent instructions
- **Controlled Behavior**: Instructions guide agent responses and prevent unwanted actions
- **Safety**: Explicit use pattern prevents accidental destructive operations
- **Debuggability**: Comprehensive logging at TRACE level for all tool usage
- **Consistency**: Standard patterns across all tools
- **Type Safety**: Pydantic validation catches errors early

### Negative

- **Boilerplate**: More code per tool (decorator, logging, Result wrapping)
- **Learning Curve**: Developers must understand Result pattern and instruction semantics
- **Verbosity**: Tool responses are more complex than simple return values
- **Dependency**: Requires ADR-004 (logging) to be implemented first

### Neutral

- **Prefix Configuration**: Adds environment variable dependency
- **Instruction Vocabulary**: Recommendations, not strict requirements
- **JSON Serialization**: Limits return types but improves interoperability

## Implementation Notes

### Integration Pattern

```python
from mcp_core.mcp_log import get_logger
from mcp_guide.tool_decorator import ExtMcpToolDecorator
from mcp_guide.result import Result

logger = get_logger(__name__)

# Create decorated tool registry
mcp = FastMCP("mcp-guide")
tools = ExtMcpToolDecorator(mcp, prefix=None)  # Uses MCP_TOOL_PREFIX env var

@tools.tool()
@log_tool_usage
async def get_project_config(project: Optional[str] = None) -> Result[dict]:
    """Get project configuration settings.

    Args:
        project: Optional project name (uses active if not provided)

    Returns:
        Result with configuration dictionary
    """
    try:
        config = await load_config(project)
        return Result(
            value=config.to_dict(),
            message="Configuration loaded successfully.",
            instruction="Review the configuration before making changes."
        )
    except FileNotFoundError as e:
        return Result(
            error="Configuration file not found",
            error_type="NotFoundError",
            exception=str(e),
            message=f"No configuration found for project: {project}",
            instruction="Present this error to the user. Do not attempt to "
                       "create a default configuration automatically."
        )
```

### Testing Considerations

- Test tool name decoration with various prefix configurations
- Test explicit use pattern rejects invalid literals
- Test Result serialization for all supported types
- Test instruction field handling in integration tests
- Mock logging to verify TRACE/DEBUG/ERROR levels

### Migration from Existing Tools

1. Wrap existing tools with `ExtMcpToolDecorator`
2. Add `@log_tool_usage` decorator
3. Convert return values to `Result[T]`
4. Add `instruction` field to guide agent behavior
5. Add explicit use pattern for destructive operations

## Dependencies

**Required:**
- ADR-004 (Logging Architecture) - MUST be implemented first for TRACE level and logging integration
- ADR-003 (Result Pattern) - Already exists, may need updates for `instruction` field

**Related:**
- Tool implementations will follow these conventions
- Documentation must reference undecorated tool names

## References

- Reference Implementation: `mcp-server-guide` production code
- ADR-003: Result Pattern and Error Handling
- ADR-004: Logging Architecture
- FastMCP Documentation: https://github.com/jlowin/fastmcp
- MCP Protocol: https://modelcontextprotocol.io/
