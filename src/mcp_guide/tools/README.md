# Tool Documentation Standards

This document establishes the standardised format for all MCP tool descriptions in mcp-guide to improve AI agent comprehension and reduce trial-and-error tool usage.

## Concise Description Format

Tool docstrings should be 2-4 sentences focusing on WHAT the tool does and WHEN to use it:

- **First sentence**: What the tool does (imperative mood)
- **Second sentence**: Key behavior or capability details
- **Optional 3rd-4th sentences**: When to use, important constraints, or context

The `build_description()` function automatically appends an `## Arguments` section from Pydantic field descriptions, providing parameter documentation.

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
@toolfunc(ExampleArgs)
async def example_tool(args: ExampleArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Process items with optional pattern filtering.

    Searches for items matching the specified name and applies optional pattern
    filtering to results. Useful for content discovery and selective processing
    workflows.
    """
    # build_description auto-appends ## Arguments section from Pydantic fields
```

## Best Practices

### Description Guidelines
- Use imperative mood ("Get", "List", "Update" not "Gets", "Lists", "Updates")
- Focus on WHAT and WHEN, not HOW
- Keep to 2-4 sentences maximum
- Avoid redundant JSON Schema/Usage/Examples sections

### Field Description Guidelines
- Always include complete Field descriptions
- Use clear, specific language
- Provide examples in descriptions where helpful
- Indicate optional vs required parameters clearly

## Validation Checklist

Before submitting tool documentation:

- [ ] Description is 2-4 sentences
- [ ] Uses imperative mood
- [ ] All Field descriptions included
- [ ] No hand-written JSON Schema/Usage/Examples sections
- [ ] Documentation follows established patterns

## Reference

This template should be referenced at the top of each tool module:

```python
# See src/mcp_guide/tools/README.md for tool documentation standards
```
