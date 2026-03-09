# ADR 010: Concise Tool Description Standard

**Status**: Accepted
**Date**: 2026-03-09
**Deciders**: Development Team
**Related**: ADR-008 (Tool Definition Conventions)

## Context

The previous 4-section tool description standard (Description + JSON Schema + Usage Instructions + Concrete Examples) created maintenance burden and redundancy:

1. **Duplicate Documentation**: Docstrings contained manually-typed JSON Schema blocks that duplicated the auto-generated `## Arguments` section that `build_description()` appends from Pydantic field descriptions at registration time
2. **Verbose Format**: The multi-section format contradicted MCP best practice, which recommends concise 1-5 sentence descriptions
3. **Low Adoption**: 24 of 28 registered tools had minimal docstrings (3-12 lines) and didn't follow the verbose standard, indicating the format was impractical

The `build_description()` function already provides complete parameter documentation by auto-generating an `## Arguments` section from Pydantic `Field(description=...)` annotations, making hand-written schema documentation unnecessary.

## Decision

Adopt a concise tool description standard:

### Docstring Format
- **2-4 sentences** focusing on WHAT the tool does and WHEN to use it
- **Imperative mood** ("Get", "List", "Update" not "Gets", "Lists", "Updates")
- **No hand-written sections** for JSON Schema, Usage Instructions, or Concrete Examples
- **Focus on purpose and behavior**, not implementation details

### Parameter Documentation
- **Single source of truth**: Pydantic `Field(description=...)` annotations
- **Auto-generated**: `build_description()` appends `## Arguments` section at registration
- **Complete coverage**: All fields must include descriptions

### Template Structure
```python
@toolfunc(ToolArgs)
async def tool_name(args: ToolArgs, ctx: Context) -> str:
    """Brief description of what the tool does.

    Additional details about key behaviors or capabilities. When to use this tool
    and any important constraints or context.
    """
    # Implementation
```

## Consequences

### Positive
- **Reduced maintenance**: Single source of parameter documentation (Pydantic fields)
- **Improved consistency**: Simple format easier to follow and maintain
- **MCP alignment**: Follows protocol best practices for concise descriptions
- **Better adoption**: 24 tools with minimal docstrings now meet the standard

### Negative
- **Less verbose examples**: No concrete usage examples in docstrings (agents must infer from descriptions and auto-generated Arguments)
- **Migration effort**: 4 verbose tools required docstring updates

### Neutral
- **No behavior changes**: Tool functionality unchanged, only documentation format
- **Agents still informed**: Complete parameter documentation via auto-generated Arguments section

## Implementation

1. Updated `src/mcp_guide/tools/README.md` template
2. Removed verbose sections from 4 tools (`client_info`, `get_project`, `get_content`, `update_documents`)
3. Improved descriptions for 14 minimal tools across category, feature flags, filesystem, and project modules
4. Renamed "Schema Guidelines" to "Field Description Guidelines" for clarity

## References

- MCP Protocol Documentation: [modelcontextprotocol.io](https://modelcontextprotocol.io/)
- Related Change: `openspec/changes/revise-tool-descriptions/`
- Tool Template: `src/mcp_guide/tools/README.md`
