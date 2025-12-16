# Design: Content Retrieval Tools

## Context

Content retrieval is the primary function of mcp-guide. The current implementation needs standardization around:
- Result pattern for consistent error handling (ADR-003)
- Tool conventions for argument schemas (ADR-008)
- Clear formatting rules for single vs multiple matches
- Agent-friendly error instructions to prevent wasted remediation attempts

## Goals

- Implement three content retrieval tools with clear responsibilities
- Use Result pattern for all responses
- Support pattern-based content filtering
- Format responses appropriately (plain markdown vs MIME multipart)
- Provide actionable error messages with agent instructions
- Design for future document-specific functionality

## Non-Goals

- Implementing document-specific retrieval (future expansion)
- Supporting non-glob pattern syntax (regex, etc.)
- Caching or performance optimization (premature)
- Supporting URI schemes other than file paths

## Decisions

### Three-Tool Design

**Decision:** Provide three separate tools: `get_content`, `get_category_content`, `get_collection_content`

**Rationale:**
- `get_content`: Convenience tool for agents that don't know if name is category or collection
- `get_category_content`: Explicit category access when agent knows the type
- `get_collection_content`: Explicit collection access when agent knows the type
- Clear separation of concerns
- Easier to document and understand

**Alternatives considered:**
- Single tool with type parameter - Less discoverable, more complex schema
- Only specific tools - No convenience option for ambiguous cases

### Pattern Parameter Design

**Decision:** Optional `pattern` parameter that overrides default patterns

**Rationale:**
- Categories have default patterns (from configuration)
- Users often want to override with specific patterns
- Optional parameter keeps simple case simple
- Consistent across all three tools

**Behavior:**
- If omitted: Use category's default patterns
- If provided: Use specified pattern instead
- Pattern syntax: Glob (standard, well-understood)

### Content Formatting Strategy

**Decision:** Single matches return plain markdown, multiple matches return MIME multipart

**Rationale:**
- Simple case stays simple (plain text)
- Complex case has proper structure (MIME standard)
- Metadata preserved when needed
- Agents can handle both formats

**Format details:**
```
Single match:
  Plain markdown content

Multiple matches:
  Content-Type: multipart/mixed; boundary="guide-boundary"

  --guide-boundary
  Content-Type: text/markdown
  Content-Location: guide://category/name/file.md
  Content-Length: 1234

  [content]

  --guide-boundary--
```

**Alternatives considered:**
- Always plain with `#` headers - Current approach, less structured
- Always MIME multipart - Overhead for single files
- JSON array - Loses markdown formatting
- Custom format - Non-standard, harder to parse

### Error Instruction Pattern

**Decision:** Include `instruction` field in Result.failure() to guide agent behavior

**Rationale:**
- Prevents agents from wasting time on futile remediation
- Provides clear guidance on next steps
- Consistent with Result pattern design (ADR-003)

**Standard instructions:**
- `not_found`: "Present this error to the user and take no further action."
- `no_matches`: "Present this error to the user so they can correct the pattern. Do NOT attempt corrective action."
- `invalid_pattern`: "Present this error to the user with pattern syntax help."
- `no_session`: "Inform user that project context is required."

### Pattern Matching Rules

**Decision:** Use glob syntax with special handling for extensionless patterns

**Rationale:**
- Glob is standard and well-understood
- Python's `glob` module provides implementation
- Extensionless pattern matching is intuitive (intro → intro.*)

**Rules:**
- `*.md` - All markdown files
- `intro` - All files named intro (any extension)
- `intro.md` - Specific file
- `**/*.py` - Recursive Python files

### Result Pattern Integration

**Decision:** All tools return `Result[str].to_json_str()`

**Rationale:**
- Consistent with ADR-003
- Rich error information
- Agent instructions included
- Type-safe value handling

**Response structure:**
```python
# Success
Result.ok(value=content_string).to_json_str()

# Failure
Result.failure(
    error="Category 'xyz' not found",
    error_type="not_found",
    instruction="Present this error to the user and take no further action."
).to_json_str()
```

## Implementation Notes

### Tool Structure

```python
async def get_content(
    category_or_collection: str,
    pattern: Optional[str] = None
) -> str:
    """Get content from category or collection."""
    session = get_current_session()
    if not session:
        return Result.failure(
            error="No active project session",
            error_type="no_session"
        ).to_json_str()

    # Try category first
    content = await get_category_content_impl(category_or_collection, pattern)
    if content.is_ok():
        return content.to_json_str()

    # Try collection
    content = await get_collection_content_impl(category_or_collection, pattern)
    return content.to_json_str()
```

### Pattern Matching Implementation

```python
def match_pattern(directory: Path, pattern: str) -> list[Path]:
    """Match files using glob pattern."""
    if '.' not in pattern:
        # Extensionless - match all extensions
        pattern = f"{pattern}.*"

    return list(directory.glob(pattern))
```

### MIME Multipart Formatting

```python
def format_multipart(matches: list[tuple[Path, str]]) -> str:
    """Format multiple matches as MIME multipart."""
    parts = []
    for path, content in matches:
        part = f"""--guide-boundary
Content-Type: text/markdown
Content-Location: guide://category/{category}/{path.name}
Content-Length: {len(content)}

{content}
"""
        parts.append(part)

    return "\n".join(parts) + "\n--guide-boundary--"
```

## Dependencies

- Result pattern implementation (ADR-003)
- Tool conventions (ADR-008)
- Session management (existing)
- Category/Collection models (existing)

## Risks / Trade-offs

**Risk:** MIME multipart format may not be parsed correctly by all agents
- **Mitigation:** Format is still readable as text
- **Mitigation:** Document format clearly
- **Mitigation:** Provide examples in guide://help

**Risk:** Pattern matching behavior may be unintuitive
- **Mitigation:** Document pattern syntax clearly
- **Mitigation:** Provide examples for common cases
- **Mitigation:** Clear error messages for invalid patterns

**Trade-off:** Three tools vs one parameterized tool
- **Benefit:** Clearer intent and discoverability
- **Cost:** More code to maintain
- **Decision:** Benefits outweigh costs for user experience

**Trade-off:** Glob patterns only (no regex)
- **Benefit:** Simpler, more predictable
- **Cost:** Less powerful for complex matching
- **Decision:** Glob sufficient for current use cases

## Migration Plan

No migration needed - new tools.

Deployment steps:
1. Implement Result pattern if not exists
2. Implement core pattern matching
3. Implement formatting functions
4. Implement three tools
5. Register with MCP server
6. Test with MCP inspector
7. Document usage

## Open Questions

None - design is complete and ready for implementation.
