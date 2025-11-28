# Tool Implementation Guide

This guide explains how to create new tools for mcp-guide following the established conventions defined in [ADR-008](../docs/adr/008-tool-definition-conventions.md).

## Quick Start

1. Create a new file in `src/mcp_guide/tools/` with `tool_` prefix
2. Define arguments class inheriting from `ToolArguments`
3. Implement tool function with `@ToolArguments.declare` decorator
4. Return `Result[T].to_json()` for rich error handling
5. Write tests in `tests/unit/mcp_guide/tools/`

## Tool Structure

### 1. Arguments Class

```python
from typing import Literal
from mcp_core.tool_arguments import ToolArguments

class MyToolArgs(ToolArguments):
    """Arguments for my_tool."""

    name: str
    action: Literal["create", "update", "delete"]
    count: int = 10  # Optional with default
```

**Features:**
- Inherits from `ToolArguments` (Pydantic BaseModel)
- Automatic validation with `extra="forbid"`
- Use `Literal` types for constrained choices
- Generates markdown schema automatically

### 2. Tool Function

```python
from typing import Any
from mcp_core.result import Result

@ToolArguments.declare
def my_tool(args: MyToolArgs) -> dict[str, Any]:
    """Tool description shown to agents.

    Detailed explanation of what the tool does.
    Include usage examples and important notes.

    Args:
        args: Tool arguments

    Returns:
        Result[dict] with operation outcome
    """
    try:
        # Tool logic here
        result_data = {"status": "success", "name": args.name}

        result = Result.ok(result_data)
        result.message = "Operation completed successfully"

        return result.to_json()

    except ValueError as e:
        result = Result.failure(
            error=str(e),
            error_type="validation",
            exception=e
        )
        result.instruction = "Check input parameters and try again"
        return result.to_json()
```

## Result[T] Pattern

The `Result[T]` pattern provides rich error handling and agent guidance.

### Success Results

```python
# Simple success
result = Result.ok({"data": "value"})

# With message
result = Result.ok(data)
result.message = "Operation completed"

# With instruction for agent
result = Result.ok(data)
result.instruction = "Next, run the validate command"
```

### Failure Results

```python
# Basic failure
result = Result.failure(
    error="File not found",
    error_type="not_found"
)

# With exception
result = Result.failure(
    error="Invalid format",
    error_type="validation",
    exception=exc
)

# With instruction to prevent remediation
result = Result.failure(
    error="Permission denied",
    error_type="permission"
)
result.instruction = "DO NOT retry. Contact administrator for access."
```

### Instruction Field Patterns

The `instruction` field controls agent behavior:

```python
# Prevent automatic remediation
result.instruction = "DO NOT attempt to fix automatically. User intervention required."

# Suggest specific fix
result.instruction = "Try using --force flag to override validation"

# Provide context
result.instruction = "This operation requires the database to be initialized first"

# Control mode
result.instruction = "Switch to read-only mode and retry"
```

## Explicit Use Pattern

For tools that should only be used with explicit user instruction:

```python
@ToolArguments.declare
def dangerous_tool(args: DangerousArgs) -> dict[str, Any]:
    """Perform dangerous operation.

    REQUIRES EXPLICIT USER INSTRUCTION: Only use when user explicitly
    requests this specific operation. Do not use automatically.

    This tool will:
    - Delete data permanently
    - Cannot be undone
    - Requires confirmation
    """
    # Implementation
```

**Guidelines:**
- Add "REQUIRES EXPLICIT USER INSTRUCTION" in docstring
- Explain why explicit instruction is needed
- List consequences of the operation

## Testing Guidelines

### Unit Tests

```python
from mcp_guide.tools.tool_my_tool import my_tool, MyToolArgs

class TestMyTool:
    """Tests for my_tool."""

    def test_success_case(self):
        """Tool should succeed with valid input."""
        args = MyToolArgs(name="test", action="create")
        result_dict = my_tool(args)

        assert result_dict["success"] is True
        assert result_dict["value"]["name"] == "test"

    def test_validation_error(self):
        """Tool should handle validation errors."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MyToolArgs(name="test", action="invalid")

    def test_instruction_field(self):
        """Tool should provide agent instructions."""
        args = MyToolArgs(name="test", action="create")
        result_dict = my_tool(args)

        if "instruction" in result_dict:
            assert len(result_dict["instruction"]) > 0
```

### Test Coverage Requirements

- Minimum 80% coverage for tool code
- Test all success paths
- Test all error conditions
- Test Literal type constraints
- Test Result pattern usage
- Test instruction field when present

## Tool Registration

Tools are automatically registered when the server starts:

1. `@ToolArguments.declare` collects the tool
2. `server.py` imports tool modules
3. `get_declared_tools()` retrieves collected tools
4. `build_tool_description()` generates descriptions
5. `ExtMcpToolDecorator` registers with FastMCP

**No manual registration needed!**

## Environment Variables

### MCP_TOOL_PREFIX

Controls tool name prefixing:

```bash
# Default: "guide"
export MCP_TOOL_PREFIX="guide"

# Tools will be named: guide_my_tool, guide_other_tool

# Disable prefix
export MCP_TOOL_PREFIX=""

# Custom prefix
export MCP_TOOL_PREFIX="custom"
```

### MCP_INCLUDE_EXAMPLE_TOOLS

Controls example tool inclusion:

```bash
# Include example tools (for development)
export MCP_INCLUDE_EXAMPLE_TOOLS="true"

# Exclude example tools (for production)
export MCP_INCLUDE_EXAMPLE_TOOLS="false"  # default
```

## Complete Example

See `src/mcp_guide/tools/tool_example.py` for a complete working example demonstrating all patterns:

- ToolArguments with Literal types
- @ToolArguments.declare decorator
- Result[T] pattern
- Instruction field usage
- Comprehensive docstring
- Explicit use pattern

## Best Practices

1. **Validation**: Use Pydantic types for automatic validation
2. **Error Handling**: Always use Result[T] pattern
3. **Instructions**: Provide clear guidance in instruction field
4. **Documentation**: Write comprehensive docstrings
5. **Testing**: Achieve >80% coverage
6. **Naming**: Use `tool_` prefix for tool files
7. **Types**: Use Literal for constrained choices
8. **Explicit Use**: Mark dangerous operations clearly

## Common Patterns

### File Operations

```python
result = Result.ok({"path": path, "content": content})
result.message = f"Read {len(content)} bytes from {path}"
```

### Validation Errors

```python
result = Result.failure(
    error=f"Invalid {field}: {value}",
    error_type="validation"
)
result.instruction = f"Valid values are: {', '.join(valid_values)}"
```

### Not Found Errors

```python
result = Result.failure(
    error=f"{resource} not found: {identifier}",
    error_type="not_found"
)
result.instruction = f"Use list_{resource}s tool to see available options"
```

### Permission Errors

```python
result = Result.failure(
    error=f"Permission denied: {operation}",
    error_type="permission"
)
result.instruction = "DO NOT retry. Check access permissions."
```

## References

- [ADR-008: Tool Definition Conventions](../docs/adr/008-tool-definition-conventions.md)
- [ADR-003: Result Pattern](../docs/adr/003-result-pattern.md)
- [Example Tool](../src/mcp_guide/tools/tool_example.py)
