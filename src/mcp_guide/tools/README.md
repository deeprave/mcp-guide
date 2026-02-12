# Tool Documentation Standards

This document establishes the standardised format for all MCP tool descriptions in mcp-guide to improve AI agent comprehension and reduce trial-and-error tool usage.

## 4-Section Documentation Format

All tools must include these four sections in their docstrings:

### 1. Description
- **First line**: ≤50 characters if possible (for clean listings)
- **Purpose**: Clear explanation of what the tool does
- **Use cases**: When and why to use this tool

### 2. JSON Schema
- **Format**: Pydantic-generated schema in code fence with type annotation
- **Content**: Complete argument structure with types and descriptions
- **Purpose**: Helps agents understand expected parameters

### 3. Usage Instructions
- **Format**: Code examples showing general usage patterns
- **Content**: How to call the tool with typical arguments
- **Purpose**: Provides concrete guidance for tool invocation

### 4. Concrete Examples
- **Format**: Code with commentary explaining the examples
- **Content**: Real-world scenarios with expected outcomes
- **Purpose**: Demonstrates practical applications

## Field Description Requirements

All Pydantic model fields must include `Field(description=...)`:

```python
class ExampleArgs(ToolArguments):
    """Arguments for example tool."""

    name: str = Field(
        ...,
        description="Name of the item to process"
    )
    pattern: str | None = Field(
        None,
        description="Optional glob pattern to filter results (e.g., '*.md')"
    )
    verbose: bool = Field(
        False,
        description="Include detailed output in response"
    )
```

## Complete Tool Documentation Example

```python
@tools.tool()
async def example_tool(args: ExampleArgs, ctx: Optional[Context] = None) -> str:
    """Process items with optional pattern filtering.

    Searches for items matching the specified name and applies
    optional pattern filtering to results. Useful for content
    discovery and selective processing workflows.

    ## JSON Schema

    ```json
    {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "description": "Name of the item to process"
        },
        "pattern": {
          "type": "string",
          "description": "Optional glob pattern to filter results (e.g., '*.md')"
        },
        "verbose": {
          "type": "boolean",
          "description": "Include detailed output in response"
        }
      },
      "required": ["name"]
    }
    ```

    ## Usage Instructions

    ```python
    # Basic usage
    await example_tool(ExampleArgs(name="docs"))

    # With pattern filtering
    await example_tool(ExampleArgs(name="docs", pattern="*.md"))

    # Verbose output
    await example_tool(ExampleArgs(name="docs", verbose=True))
    ```

    ## Concrete Examples

    ```python
    # Example 1: Process documentation category
    result = await example_tool(ExampleArgs(name="docs"))
    # Returns: List of all items in docs category

    # Example 2: Filter markdown files only
    result = await example_tool(ExampleArgs(
        name="docs",
        pattern="*.md"
    ))
    # Returns: Only .md files from docs category

    # Example 3: Detailed processing information
    result = await example_tool(ExampleArgs(
        name="docs",
        verbose=True
    ))
    # Returns: Items with processing metadata and statistics
    ```
    """
```

## Best Practices

### Description Guidelines
- Keep first line concise and descriptive
- Use active voice ("Creates", "Lists", "Updates")
- Explain the tool's primary purpose clearly
- Include context about when to use the tool

### Schema Guidelines
- Always include complete Field descriptions
- Use clear, specific language
- Provide examples in descriptions where helpful
- Indicate optional vs required parameters clearly

### Usage Guidelines
- Show common usage patterns
- Include parameter variations
- Demonstrate typical argument combinations
- Keep examples realistic and practical

### Example Guidelines
- Use real-world scenarios
- Include expected outcomes
- Show different use cases
- Add explanatory comments

## Validation Checklist

Before submitting tool documentation:

- [ ] First line ≤50 characters (if possible)
- [ ] All four sections present and complete
- [ ] All Field descriptions included
- [ ] JSON schema matches Pydantic model
- [ ] Usage examples are runnable
- [ ] Concrete examples include outcomes
- [ ] Documentation follows established patterns

## Reference

This template should be referenced at the top of each tool module:

```python
# See src/mcp_guide/tools/README.md for tool documentation standards
```
