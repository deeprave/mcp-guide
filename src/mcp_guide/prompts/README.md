# Prompt Documentation Standards

This document establishes the standardised format for all MCP prompt descriptions in mcp-guide to improve AI agent comprehension and reduce trial-and-error prompt usage.

## 4-Section Documentation Format

All prompts must include these four sections in their docstrings:

### 1. Description
- **First line**: ≤50 characters if possible (for clean listings)
- **Purpose**: Clear explanation of what the prompt does
- **Use cases**: When and why to use this prompt

### 2. Conceptual Schema
- **Format**: Show `*args` interface (not actual arg1...argF implementation)
- **Content**: Conceptual argument structure that agents should understand
- **Purpose**: Helps agents understand expected parameters without exposing ugly implementation

### 3. Usage Instructions
- **Format**: Code examples showing `@prompt_name` syntax
- **Content**: How to invoke the prompt with typical arguments
- **Purpose**: Provides concrete guidance for prompt usage

### 4. Concrete Examples
- **Format**: Real prompt invocations with commentary
- **Content**: Practical scenarios with expected outcomes
- **Purpose**: Demonstrates real-world applications

## Varargs Implementation Handling

Due to MCP/FastMCP limitations, prompts use `arg1, arg2, arg3...argF` (up to 15 arguments) internally, but documentation should **pretend** this is a clean varargs interface:

### Implementation Reality
```python
async def guide(
    arg1: Optional[str] = None,
    arg2: Optional[str] = None,
    arg3: Optional[str] = None,
    # ... up to argF
    ctx: Optional["Context"] = None,
) -> str:
```

### Documentation Interface
```python
async def guide(*args) -> str:
    """Direct access to guide content.

    Args:
        *args: Variable arguments for content specification
    """
```

## Complete Prompt Documentation Example

```python
@prompts.prompt()
async def example_prompt(*args) -> str:
    """Process content with flexible argument handling.

    Accepts variable arguments to process content from multiple
    sources. Arguments can be category names, collection names,
    or pattern specifications for flexible content retrieval.

    ## Conceptual Schema

    ```python
    def example_prompt(*args: str) -> str:
        \"\"\"
        Args:
            *args: Variable string arguments for content processing
                  - Category names (e.g., 'docs', 'examples')
                  - Collection names (e.g., 'getting-started')
                  - Pattern specifications (e.g., 'docs/*.md')

        Returns:
            JSON string with processed content results
        \"\"\"
    ```

    ## Usage Instructions

    ```bash
    # Single argument
    @example_prompt docs

    # Multiple arguments
    @example_prompt docs examples

    # Mixed category and pattern
    @example_prompt docs examples/*.md

    # Collection processing
    @example_prompt getting-started advanced-topics
    ```

    ## Concrete Examples

    ```bash
    # Example 1: Single category processing
    @example_prompt docs
    # Processes all content from 'docs' category
    # Returns: Formatted content from docs directory

    # Example 2: Multiple category processing
    @example_prompt docs examples tutorials
    # Processes content from multiple categories
    # Returns: Combined content from all specified categories

    # Example 3: Pattern-based filtering
    @example_prompt docs/*.md examples/*.py
    # Processes specific file types from categories
    # Returns: Filtered content matching specified patterns

    # Example 4: Collection processing
    @example_prompt getting-started
    # Processes all categories in the collection
    # Returns: Complete collection content in organised format
    ```
    """
```

## Best Practices

### Description Guidelines
- Keep first line concise and descriptive
- Use active voice ("Processes", "Retrieves", "Generates")
- Explain the prompt's primary purpose clearly
- Include context about when to use the prompt

### Schema Guidelines
- Always show `*args` interface in documentation
- Never expose `arg1...argF` implementation details
- Use clear, specific language for argument descriptions
- Indicate argument flexibility and variations

### Usage Guidelines
- Show `@prompt_name` invocation syntax
- Include single and multiple argument examples
- Demonstrate typical argument patterns
- Keep examples realistic and practical

### Example Guidelines
- Use real prompt invocations
- Include expected outcomes
- Show different argument combinations
- Add explanatory comments about results

## Argument Processing Pattern

Prompts should document how they handle the variable arguments conceptually:

```python
# Conceptual processing (document this)
def process_args(*args):
    """Process variable arguments into meaningful operations."""
    for arg in args:
        if is_category(arg):
            process_category(arg)
        elif is_collection(arg):
            process_collection(arg)
        elif is_pattern(arg):
            process_pattern(arg)

# Actual implementation (hide this)
argv = ["prompt_name"]
for arg in [arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, argA, argB, argC, argD, argE, argF]:
    if arg is None:
        break
    argv.append(arg)
```

## Validation Checklist

Before submitting prompt documentation:

- [ ] First line ≤50 characters (if possible)
- [ ] All four sections present and complete
- [ ] Conceptual schema uses `*args` (not arg1...argF)
- [ ] Usage examples show `@prompt_name` syntax
- [ ] Concrete examples include expected outcomes
- [ ] Implementation details are hidden from documentation
- [ ] Documentation follows established patterns

## Reference

This template should be referenced at the top of each prompt module:

```python
# See src/mcp_guide/prompts/README.md for prompt documentation standards
```
