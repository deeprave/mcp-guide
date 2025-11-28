# Design: guide:// URI Scheme

## Context

MCP protocol supports resource discovery and access through `resources/list` and `resources/read` methods. This provides a declarative way for agents to discover and access content, complementing the imperative tool-based approach.

## Goals

- Enable resource-based access to guide content
- Provide clear URI patterns for different content types
- Maintain consistency with existing tool-based access
- Support both static resources and dynamic templates

## Non-Goals

- Replacing tool-based access (both approaches coexist)
- Implementing content retrieval logic (delegated to content tools)
- Supporting URI schemes other than guide://

## Decisions

### URI Pattern Design

**Decision:** Use hierarchical URI structure with clear resource type prefixes

Patterns:
```
guide://help
guide://collection/{id}
guide://category/{name}
guide://category/{name}/{docId}
guide://document/{context}/{docId}
```

**Rationale:**
- Clear resource type identification
- Natural hierarchy (category → document)
- Consistent with REST-like patterns
- Easy to parse and validate

**Alternatives considered:**
- Flat structure (guide://{type}/{id}) - Less intuitive hierarchy
- Query parameters (guide://category?name=x) - More complex parsing
- Path-only (guide://category/name/doc) - Ambiguous resource types

### Category vs Document Semantics

**Decision:** `guide://category/{name}/{docId}` searches both documents and patterns, while `guide://document/{context}/{docId}` searches only documents.

**Rationale:**
- Category access is exploratory (user may want patterns)
- Document access is specific (user knows what they want)
- Provides both broad and narrow search options
- Matches existing tool behavior

### Content Format

**Decision:** Single matches return plain markdown, multiple matches return MIME multipart.

**Rationale:**
- Simple case stays simple (plain markdown)
- Complex case has proper structure (MIME multipart)
- Standard format for aggregated content
- Metadata preserved per part

**Alternatives considered:**
- Always use MIME multipart - Adds overhead for single files
- Custom separator format - Non-standard, harder to parse
- JSON array of content - Loses markdown formatting

### Resource vs Template

**Decision:** Static resources for fixed URIs (help), templates for parameterized URIs (collections, categories).

**Rationale:**
- Follows MCP protocol design
- Enables agent discovery of available patterns
- Reduces resource list size
- Clear distinction between concrete and dynamic resources

## Implementation Notes

### URI Parsing

```python
def parse_guide_uri(uri: str) -> dict:
    """Parse guide:// URI into components."""
    # Validate scheme
    # Extract resource type
    # Extract parameters
    # Return structured dict
```

### Resource List Response

```python
{
    "resources": [
        {
            "uri": "guide://help",
            "name": "Guide URI Help",
            "mimeType": "text/markdown"
        }
    ],
    "resourceTemplates": [
        {
            "uriTemplate": "guide://collection/{id}",
            "name": "Collection by ID",
            "mimeType": "text/markdown"
        },
        # ... more templates
    ]
}
```

### Content Delegation

Resource read handler delegates to content retrieval:
1. Parse URI
2. Extract parameters
3. Call appropriate content function
4. Format response based on result count

## Dependencies

- Content retrieval implementation (separate change)
- Result pattern for error handling (ADR-003)
- Existing category/collection models

## Risks / Trade-offs

**Risk:** MIME multipart format may not be parsed by all agents
- **Mitigation:** Format is still readable as text if not parsed
- **Mitigation:** Document format in guide://help

**Risk:** URI pattern ambiguity between category and collection names
- **Mitigation:** Document-only pattern uses explicit context resolution
- **Mitigation:** Clear error messages for ambiguous cases

**Trade-off:** Two access methods (tools vs resources) increases complexity
- **Benefit:** Flexibility for different agent workflows
- **Benefit:** Standard MCP resource pattern support

## Migration Plan

No migration needed - additive feature only.

Deployment steps:
1. Implement resource handlers
2. Test with MCP inspector
3. Document in README
4. Update examples

## Open Questions

None - deferred content retrieval details to separate change.
