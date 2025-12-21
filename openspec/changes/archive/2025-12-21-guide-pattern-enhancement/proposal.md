# Change: Guide Pattern Enhancement - Unified Content Retrieval

## Why

Current content retrieval is fragmented across multiple tools with limited flexibility:

1. **Limited Pattern Support**: Categories use fixed default patterns; no multi-pattern support within categories
2. **Inflexible Collections**: Collections can only group categories, not specify per-category patterns or expressions
3. **Separate Tools**: `get_content`, `get_category_content`, and `get_collection_content` create API fragmentation
4. **No Expression Syntax**: Users cannot specify complex content selection without creating numerous collections
5. **Inconsistent Results**: Different tools handle "no content found" scenarios differently

Users need a unified, expressive syntax for content retrieval that supports:
- Multi-pattern selection within categories
- Per-category pattern overrides in collections
- Complex expressions with boolean logic
- Single tool interface for all content access scenarios

## What Changes

### Phase 1: Slash Syntax Support
Enable `get_content("<category>/<pattern>")` as shorthand for `get_content("<category>", "<pattern>")`:

```python
# New syntax (equivalent to existing two-parameter form)
get_content("lang/python")           # category="lang", pattern="python"
get_content("docs/api/v1/auth")      # category="docs", pattern="api/v1/auth"
```

### Phase 2: Multi-Pattern Category Support
Extend categories to support multiple patterns with `+` separator:

```python
# Multiple patterns within same category
get_content("lang/python+java+rust")        # All three patterns in lang category
get_content("docs/api+tutorial+reference")  # Multiple doc types
```

### Phase 3: Unified Content Retrieval
Consolidate all content access through single `get_content` tool with expression support:

```python
# Multi-category expressions (comma-separated)
get_content("lang/python+java,docs/api,guidelines")

# Collections as expression macros
get_content("quick-start")  # Expands to collection's stored expression

# Mixed collections and categories
get_content("quick-start,lang/rust,context/openspec")
```

### Phase 4: Enhanced Collections
Collections store expressions and support per-category pattern overrides:

```yaml
collections:
  quick-start:
    description: "Getting started documentation"
    categories:
      - api-reference: ["overview*.md", "quickref*.md"]  # Pattern override
      - user-guides: ["getting-started*.md"]             # Pattern override
      - tutorials                                         # Use default patterns
```

### Phase 5: Tool Consolidation
- Remove `get_collection_content` tool (functionality absorbed by `get_content`)
- Keep `get_category_content` for backward compatibility (delegates to `get_content`)
- Single unified content handler with consistent error handling

## Impact

- **Affected specs**: `tool-infrastructure`
- **Affected code**:
  - `src/mcp_guide/tools/tool_category.py` - Enhanced pattern parsing and multi-pattern support
  - `src/mcp_guide/tools/tool_collection.py` - Pattern override support, eventual removal of separate tool
  - `src/mcp_guide/models.py` - Collection model extension for pattern overrides
  - `src/mcp_guide/core/result.py` - Fix Result.ok() method signature
  - New expression parser module
- **Breaking changes**:
  - **NONE** - All existing syntax remains supported
  - `get_collection_content` will be deprecated but continue working
- **Benefits**:
  - Unified, intuitive content access syntax
  - Flexible multi-pattern support
  - Collections become powerful expression macros
  - Consistent error handling across all scenarios
  - Reduced API surface area
  - Better user experience with natural syntax

## Implementation Phases

### Phase 1: Foundation (Slash Syntax)
- Parse `category/pattern` syntax in `get_content`
- Maintain full backward compatibility
- Fix `Result.ok()` method signature inconsistency

### Phase 2: Multi-Pattern Support
- Implement `+` separator for multiple patterns within categories
- Extend pattern matching to handle pattern lists
- Add validation for pattern syntax

### Phase 3: Expression Parsing
- Implement comma-separated multi-category expressions
- Add expression parser with proper precedence rules
- Support complex nested expressions

### Phase 4: Collection Enhancement
- Extend Collection model for pattern overrides
- Implement three-tier pattern resolution (call > collection > category)
- Update collection management tools

### Phase 5: Tool Consolidation
- Migrate `get_collection_content` functionality to `get_content`
- Deprecate `get_collection_content` with migration guidance
- Ensure consistent behavior across all scenarios

## Acceptance Criteria

### Phase 1
- [ ] `get_content("category/pattern")` works equivalently to `get_content("category", "pattern")`
- [ ] Slash parsing handles paths correctly (only first `/` is delimiter)
- [ ] `Result.ok()` method accepts optional value parameter
- [ ] All existing functionality remains unchanged

### Phase 2
- [ ] `get_content("category/pattern1+pattern2")` retrieves content matching any pattern
- [ ] Multi-pattern syntax works with slash syntax
- [ ] Pattern validation handles complex patterns correctly

### Phase 3
- [ ] Comma-separated expressions work: `get_content("cat1/pat1,cat2/pat2")`
- [ ] Mixed syntax works: `get_content("cat1/pat1+pat2,cat2,cat3/pat3")`
- [ ] Expression parser handles edge cases and provides clear errors

### Phase 4
- [ ] Collections support pattern overrides in YAML configuration
- [ ] Three-tier pattern resolution works correctly
- [ ] Collection management tools support pattern overrides
- [ ] Backward compatibility maintained for existing collections

### Phase 5
- [ ] `get_content` handles all collection scenarios
- [ ] `get_collection_content` deprecated with clear migration path
- [ ] Consistent error handling across all content retrieval scenarios
- [ ] Performance equivalent or better than separate tools

## Migration Strategy

### Immediate (Phase 1-3)
- All existing code continues working unchanged
- New syntax available as enhancement
- No breaking changes

### Medium-term (Phase 4-5)
- `get_collection_content` marked as deprecated
- Documentation updated to recommend `get_content`
- Migration examples provided

### Long-term
- `get_collection_content` removed in future major version
- Single unified content access pattern established
