# Change: Collections with Per-Category Pattern Overrides

**Status**: Proposed
**Date**: 2025-12-08

## Why

Currently, collections group categories together, but all categories use their default patterns when accessed through a collection. This limits flexibility when you want to:

- Access only specific file types from certain categories within a collection
- Create focused collections that filter content differently than the category defaults
- Build specialized views of content without creating duplicate categories

**Example Use Case:**
- Collection `docs` includes categories `[api-reference, user-guides, tutorials]`
- Want collection `quick-start` with `[api-reference/*.md, user-guides/getting-started*.md, tutorials/intro*.md]`
- Currently requires creating separate categories or manual pattern overrides on every call

## What Changes

### Data Model Enhancement

Extend the `Collection` model to support optional per-category pattern overrides:

**Current:**
```python
@dataclass
class Collection:
    name: str
    description: Optional[str]
    categories: list[str]  # Just category names
```

**Proposed:**
```python
@dataclass
class Collection:
    name: str
    description: Optional[str]
    categories: list[str | dict[str, list[str]]]  # Name or {name: patterns}
```

**Configuration Format:**

```yaml
collections:
  basic-collection:
    description: "Uses default patterns"
    categories:
      - api-reference
      - user-guides

  filtered-collection:
    description: "Overrides patterns for specific categories"
    categories:
      - api-reference: ["*.md"]           # Only markdown docs
      - user-guides                        # Use default patterns
      - tutorials: ["intro*.md", "quick*.md"]  # Only intro/quick start tutorials
```

### Tool Behavior Changes

**`get_collection_content` tool:**
- When pattern override specified in collection definition, use it instead of category default
- When no override specified, use category's default patterns
- User can still override at call time with `pattern` parameter (highest priority)

**Priority Order:**
1. Tool call `pattern` parameter (if provided)
2. Collection's per-category pattern override (if defined)
3. Category's default patterns

**Other collection tools:**
- `collection_add`: Accept optional pattern overrides in category specifications
- `collection_change`: Support updating pattern overrides
- `collection_update`: Support adding/removing categories with pattern overrides
- `collection_list`: Display pattern overrides in verbose mode

### Validation

- Pattern overrides must be valid glob patterns
- Category names must exist in project
- Pattern overrides are optional (backward compatible)

## Impact

- **Backward Compatibility**: YES - existing collections without pattern overrides work unchanged
- **Affected Tools**:
  - `get_collection_content` - pattern resolution logic
  - `collection_add` - accept pattern overrides
  - `collection_change` - handle pattern overrides
  - `collection_update` - modify pattern overrides
  - `collection_list` - display pattern overrides
- **Configuration Format**: Extended (backward compatible)
- **Breaking Changes**: None

## Implementation Approach

### Phase 1: Data Model
- Update `Collection` model to support pattern overrides
- Update YAML serialization/deserialization
- Add validation for pattern overrides

### Phase 2: Content Retrieval
- Update `get_collection_content` to resolve patterns with priority order
- Add tests for pattern override resolution

### Phase 3: Collection Management Tools
- Update `collection_add` to accept pattern overrides
- Update `collection_change` to handle pattern overrides
- Update `collection_update` to modify pattern overrides
- Update `collection_list` to display pattern overrides

### Phase 4: Testing & Documentation
- Integration tests for pattern override scenarios
- Update tool documentation
- Add examples to README

## Examples

### Creating Collection with Pattern Overrides

```python
# Via collection_add tool
{
  "name": "getting-started",
  "description": "Quick start documentation",
  "categories": [
    {"name": "api-reference", "patterns": ["overview*.md", "quickref*.md"]},
    {"name": "user-guides", "patterns": ["getting-started*.md", "installation*.md"]},
    {"name": "tutorials", "patterns": ["intro*.md", "hello-world*.md"]}
  ]
}
```

### Accessing Collection Content

```python
# Uses pattern overrides from collection definition
get_collection_content(collection="getting-started")

# User override takes precedence
get_collection_content(collection="getting-started", pattern="*.pdf")
```

### Configuration Example

```yaml
collections:
  all-docs:
    description: "All documentation"
    categories:
      - api-reference
      - user-guides
      - tutorials

  markdown-only:
    description: "Markdown documentation only"
    categories:
      - api-reference: ["*.md"]
      - user-guides: ["*.md"]
      - tutorials: ["*.md", "*.markdown"]
```

## Open Questions

1. Should pattern overrides be validated against category's directory structure?
2. Should we support pattern exclusions (e.g., `["*.py", "!test_*.py"]`)?
3. Should verbose mode show which patterns are being used (default vs override)?

## Related

- ADR-003: Result Pattern Response
- ADR-008: Tool Definition Conventions
- Existing: Collection Management Tools
- Existing: Content Retrieval Tools
