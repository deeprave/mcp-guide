# Design: guide:// URI Scheme

## Context

MCP protocol supports resource discovery and access through `resources/list` and `resources/read` methods. This provides a declarative way for agents to discover and access content, complementing the imperative tool-based approach.

## Goals

- Enable resource-based access to guide content
- Provide simple URI pattern for content access
- Maintain consistency with existing tool-based access
- Delegate to existing content retrieval system

## Non-Goals

- Replacing tool-based access (both approaches coexist)
- Complex URI patterns or resource types
- MIME multipart formatting
- Help resource generation

## Decisions

### URI Pattern Design

**Decision:** Use single URI pattern `guide://collection/document`

**Rationale:**
- Simple and clear
- Maps directly to existing content system
- Easy to parse and validate
- Consistent with tool-based access

**Alternatives considered:**
- Multiple resource types (help, category, document) - Added complexity without clear benefit
- Query parameters - More complex parsing
- Hierarchical patterns - Unnecessary for current use cases

### Content Delegation

**Decision:** Direct delegation to `internal_get_content` function

**Rationale:**
- Reuses existing, tested content retrieval logic
- Maintains consistency between tools and resources
- No duplication of content handling code
- Simple error propagation

### Content Format

**Decision:** Plain text/markdown responses only

**Rationale:**
- Simple implementation
- Matches existing tool behavior
- No need for complex MIME formatting
- Easy for agents to consume

**Alternatives considered:**
- MIME multipart for multiple documents - Added complexity without clear benefit
- JSON formatting - Loses markdown structure
- Custom separators - Non-standard approach

## Implementation

### URI Parsing

```python
@dataclass
class GuideUri:
    collection: str
    document: Optional[str] = None

def parse_guide_uri(uri: str) -> GuideUri:
    # Parse guide://collection/document format
    # Validate scheme and extract components
```

### Resource Handler

```python
@mcp_server.resource("guide://{collection}/{document}")
async def guide_resource(collection: str, document: str = "", ctx=None) -> str:
    # Create ContentArgs and delegate to internal_get_content
    # Return content text or error message
```

### Server Integration

Resource handler registered via FastMCP decorator pattern during server initialization.

## Dependencies

- Existing `internal_get_content` function
- FastMCP resource decorator support
- ContentArgs model from content tools

## Risks / Trade-offs

**Trade-off:** Simplified design may not support all future use cases
- **Benefit:** Faster implementation and testing
- **Benefit:** Easier to understand and maintain
- **Mitigation:** Can extend pattern in future if needed

**Risk:** Single URI pattern may be limiting
- **Mitigation:** Pattern supports both collection-only and collection/document access
- **Mitigation:** Existing tool-based access provides full functionality

## Migration Plan

No migration needed - additive feature only.

Implementation completed:
1. ✅ URI parser implementation
2. ✅ Resource handler implementation
3. ✅ Server integration
4. ✅ Unit and integration tests
5. ✅ Code quality checks
