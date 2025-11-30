# ADR-008: MCP Tool Definition Conventions

**Date:** 2025-11-27
**Status:** Accepted
**Dependencies:** ADR-001 (Tool Naming Convention), ADR-004 (Logging Architecture), ADR-003 (Result Pattern)
**Revised:** 2025-11-27 - Integrated logging into decorator (removed separate log_tool_usage decorator)

## Revision History

### 2025-11-30: ToolArguments Automatic Transformation
**What Changed:** Enhanced decorator to automatically construct and validate ToolArguments instances from FastMCP kwargs

**Why:** Previous pattern required manual synchronization between ToolArguments schema and function signature - every field had to be duplicated. This was error-prone and violated DRY principle. The ToolArguments class was only used for documentation generation, not runtime validation or transformation.

**Impact:**
- Decorator now detects if function expects ToolArguments instance (inspects first parameter type)
- Automatically constructs ToolArguments from kwargs with Pydantic validation
- Function signature simplified: `func(args: ToolArgs, ctx: Context = None)`
- Single source of truth: ToolArguments class defines schema once
- Automatic validation: Pydantic validates all inputs at runtime
- Validation errors converted to Result.failure with structured details
- Legacy pattern (individual parameters) still supported for backward compatibility

**New Pattern (Preferred):**
```python
@tools.tool(CategoryListArgs)
async def category_list(args: CategoryListArgs, ctx: Context = None) -> str:
    if args.verbose:  # Type-safe access
        ...
```

**Legacy Pattern (Deprecated but supported):**
```python
@tools.tool(CategoryListArgs)
async def category_list(verbose: bool = True, ctx: Any = None) -> str:
    # Must manually keep signature in sync with CategoryListArgs
```

### 2025-11-29: Lazy Tool Registration
**What Changed:** Replaced `@ToolArguments.declare` decorator with lazy registration via constructor

**Why:** Import-time decorator registration caused test isolation issues - tools registered in one test polluted global state for subsequent tests. Lazy registration via constructor ensures tools are only registered when actually instantiated, preventing cross-test pollution and enabling proper cleanup.

**Impact:**
- Tool functions no longer use `@ToolArguments.declare` decorator
- Args classes must call `super().__init__(handler=func, **data)` in constructor
- Registration happens on first instantiation, not at import time
- Tests have proper isolation - importing a tool module doesn't register it
- `get_declared_tools()` returns `Dict[str, tuple[Type[ToolArguments], Callable]]`

### 2025-11-27: Integrated Logging Approach
**What Changed:** Combined `log_tool_usage` decorator into `ExtMcpToolDecorator`

**Why:** Simplifies usage and reduces boilerplate. Instead of requiring two decorators (`@tools.tool()` + `@log_tool_usage`), logging is now automatic when using `@tools.tool()`. This decision was made during implementation planning to reduce developer friction and ensure consistent logging across all tools without manual decorator application.

**Impact:** Tools now only need single decorator. Logging happens automatically for all tool invocations.

## Context

MCP servers expose tools to AI agents, but without conventions, several problems arise:

1. **Naming Collisions**: Multiple MCP servers may define tools with the same name
2. **Agent Behavior Control**: Need to guide agent responses and prevent unwanted remediation attempts
3. **Inconsistent Error Handling**: No standard way to communicate errors vs user messages vs agent instructions
4. **Tool Discovery**: Agents need clear, complete information to decide when to use a tool
5. **Destructive Actions**: Need explicit user consent for potentially dangerous operations

This ADR establishes conventions for tool definition, naming, descriptions, and response handling in mcp-guide.

## Decision

### 1. Tool Name Decoration with Integrated Logging

All MCP tools MUST use a custom decorator that adds an optional prefix to tool names and automatically logs all invocations.

**Note:** This implements the tool naming convention from ADR-001, which decided to use namespaced tool names with configurable prefix to prevent naming conflicts across MCP servers.

```python
from mcp_core.mcp_log import get_logger

logger = get_logger(__name__)

class ExtMcpToolDecorator:
    """Extended MCP tool decorator with prefix and automatic logging."""

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

**Prefix Configuration:**
- Default prefix from `MCP_TOOL_PREFIX` environment variable (default: "guide")
- Per-tool override via `prefix` kwarg in decorator
- Empty string disables prefix (for agents that auto-prefix)

**Automatic Logging:**
- TRACE level: Tool invocation and successful completion (async)
- DEBUG level: Successful completion (sync)
- ERROR level: Tool failures with exception details
- No manual decorator application required

**Documentation Convention:**
- All documentation, code, specifications, and references MUST use the **undecorated** tool name
- Prefix is an implementation detail for runtime collision avoidance

### 2. Tool Descriptions

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

### 3. Result Pattern

All tools MUST return `Result[T]` as defined in ADR-003, where T is JSON-serializable.

**Reference:** See [ADR-003: Result Pattern for Tool and Prompt Responses](003-result-pattern-response.md) for:
- Complete Result definition with all fields
- Field usage patterns for success and failure responses
- Instruction field semantics and common patterns
- Exception handling and JSON serialization
- Helper methods: `ok()`, `failure()`, `is_ok()`, `is_failure()`, `to_json()`, `to_json_str()`

**Tool-Specific Usage:**

Tools should use the `instruction` field to guide agent behavior. Common patterns include preventing unwanted error remediation, suggesting specific fixes, controlling operational modes, and enforcing safety boundaries. See ADR-003 for detailed instruction patterns and examples.

### 4. Instruction Field Semantics

The `instruction` field controls agent behavior on receiving the response:

**Common Instruction Patterns:**

```python
# Error handling - prevent remediation
Result(
    success=False,
    error="File not found",
    error_type="NotFoundError",
    message="The requested file does not exist.",
    instruction="Present this error to the user and take no further action. "
                "Do not attempt to create the file or suggest alternatives."
)

# Error handling - suggest remediation
Result(
    success=False,
    error="Invalid format",
    error_type="ValidationError",
    message="The document format is invalid.",
    instruction="The document must be in markdown format. "
                "Suggest converting the content to markdown before retrying."
)

# Mode switching
Result(
    success=True,
    value={"status": "planning_required"},
    message="This operation requires planning.",
    instruction="Switch to PLANNING mode. Create a detailed plan before "
                "making any changes to the project."
)

# Operational boundaries
Result(
    success=True,
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

### 5. ToolArguments Automatic Transformation

The decorator automatically constructs and validates ToolArguments instances from FastMCP kwargs, eliminating signature duplication.

**Pattern Detection:**
The decorator inspects the function signature to determine which pattern to use:
- If first parameter is a ToolArguments subclass → construct instance and validate
- Otherwise → pass kwargs through (legacy pattern)

**New Pattern (Preferred):**
```python
class CategoryListArgs(ToolArguments):
    """Arguments for category_list tool."""
    verbose: bool = True
    include_hidden: bool = False

@tools.tool(CategoryListArgs)
async def category_list(args: CategoryListArgs, ctx: Context = None) -> str:
    """List all categories in the current project."""
    if args.verbose:
        # Type-safe access to validated arguments
        categories = get_detailed_categories(include_hidden=args.include_hidden)
    else:
        categories = get_category_names()
    return Result.ok(categories).to_json_str()
```

**Benefits:**
- **Single Source of Truth**: ToolArguments class defines schema once
- **Automatic Validation**: Pydantic validates all inputs at runtime
- **Type Safety**: IDE autocomplete and type checking work correctly
- **Maintainability**: Add/modify fields in one place only
- **Error Quality**: Structured validation errors for agents

**Context Parameter Handling:**
- `ctx: Context` is always extracted from kwargs (never part of ToolArguments)
- FastMCP injects ctx, not from JSON
- Passed as separate keyword argument to function
- Optional parameter (defaults to None)

**Validation Error Handling:**
```python
# Decorator automatically catches ValidationError
try:
    tool_args = args_class(**kwargs)
    result = await func(tool_args, ctx=ctx)
except ValidationError as e:
    # Converted to Result.failure with field-level details
    error_details = {
        "validation_errors": [
            {"field": err["loc"][0], "message": err["msg"]}
            for err in e.errors()
        ]
    }
    return Result.failure(
        f"Invalid arguments: {e}",
        error_type="validation_error",
        data=error_details
    ).to_json_str()
```

**Legacy Pattern (Deprecated):**
```python
@tools.tool(CategoryListArgs)
async def category_list(verbose: bool = True, ctx: Any = None) -> str:
    """Legacy pattern - must manually sync signature with ToolArguments."""
    # Decorator passes kwargs through unchanged
```

The legacy pattern is supported for backward compatibility but should not be used for new tools.

### 6. Pydantic Validation and Lazy Registration

Tools MUST use Pydantic models for argument validation with lazy registration pattern:

```python
from pydantic import BaseModel, Field
from mcp_core.tool_arguments import ToolArguments

class CreateDocumentArgs(ToolArguments):
    """Arguments for document creation."""
    category_dir: str = Field(..., description="Category directory path")
    name: str = Field(..., min_length=1, max_length=100, description="Document name")
    content: str = Field(..., description="Document content")
    explicit_action: Literal["CREATE_DOCUMENT"] = Field(
        ...,
        description="Must be 'CREATE_DOCUMENT' to confirm intent"
    )

    def __init__(self, handler: Callable, **data):
        super().__init__(handler=handler, **data)

def create_document(args: CreateDocumentArgs) -> Result[dict]:
    """Create a new document."""
    # Implementation
    pass

# Usage - registration happens on instantiation
args = CreateDocumentArgs(handler=create_document, category_dir="docs", name="test.md",
                          content="...", explicit_action="CREATE_DOCUMENT")
```

**Lazy Registration Pattern:**
- Tool registration happens when args class is first instantiated, not at import time
- Handler function is passed to args constructor
- Prevents test isolation issues from import-time side effects
- `get_declared_tools()` returns `Dict[str, tuple[Type[ToolArguments], Callable]]`


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

@tools.tool()  # Logging happens automatically
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
            success=True,
            value=config.to_dict(),
            message="Configuration loaded successfully.",
            instruction="Review the configuration before making changes."
        )
    except FileNotFoundError as e:
        return Result(
            success=False,
            error="Configuration file not found",
            error_type="NotFoundError",
            exception=e,
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
- Test automatic logging at TRACE/DEBUG/ERROR levels
- Mock logging to verify correct log levels and messages

### Migration from Existing Tools

1. Wrap existing tools with `ExtMcpToolDecorator`
2. Convert return values to `Result[T]`
3. Add `instruction` field to guide agent behavior
4. Add explicit use pattern for destructive operations
5. Logging is automatic - no additional decorator needed

## Dependencies

**Required:**
- ADR-004 (Logging Architecture) - MUST be implemented first for TRACE level and logging integration
- ADR-003 (Result Pattern) - Provides Result[T] type with success field, instruction field, and JSON serialization

**Related:**
- Tool implementations will follow these conventions
- Documentation must reference undecorated tool names

## References

- ADR-001: Tool Naming Convention
- ADR-003: Result Pattern for Tool and Prompt Responses
- ADR-004: Logging Architecture
- Reference Implementation: `mcp-server-guide` production code
- FastMCP Documentation: https://github.com/jlowin/fastmcp
- MCP Protocol: https://modelcontextprotocol.io/

