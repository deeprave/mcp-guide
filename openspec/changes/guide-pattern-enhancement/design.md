# Guide Pattern Enhancement Design

## Context

This change unifies and enhances the content retrieval system by combining two existing proposals:
1. **category-collection-enhancement**: Expression-based content retrieval with boolean logic
2. **collections-with-patterns**: Per-category pattern overrides in collections

The unified approach provides a single, expressive API for all content access scenarios while maintaining full backward compatibility.

## Goals / Non-Goals

### Goals
- Unified content access through single `get_content` tool
- Intuitive slash syntax: `get_content("category/pattern")`
- Multi-pattern support: `get_content("category/pattern1+pattern2")`
- Multi-category expressions: `get_content("cat1/pat1,cat2/pat2")`
- Collections with pattern overrides and expression storage
- Consistent error handling across all scenarios
- Full backward compatibility during transition

### Non-Goals
- Breaking existing API compatibility
- Complex query languages or SQL-like syntax
- Real-time content indexing or search
- Content transformation or filtering beyond pattern matching

## Decisions

### Expression Syntax Design

**Decision**: Use hierarchical separator approach with clear precedence

**Syntax Rules:**
1. **Comma (`,`)**: Separates different category/collection expressions (lowest precedence)
2. **Slash (`/`)**: Separates category from pattern(s) within each expression
3. **Plus (`+`)**: Separates multiple patterns within same category (highest precedence)

**Examples:**
```python
get_content("lang/python+java,docs/api,guidelines")
# Parsed as:
# 1. lang/(python+java)  - lang category with patterns [python, java]
# 2. docs/api            - docs category with pattern api
# 3. guidelines          - guidelines category with default patterns
```

**Rationale:**
- Natural hierarchy: category → patterns → multiple patterns
- Intuitive for users familiar with file paths
- Clear precedence rules prevent ambiguity
- Extensible for future enhancements

### Pattern Resolution Priority

**Decision**: Three-tier resolution with clear override hierarchy

**Priority Order:**
1. **Tool call parameter** (highest): `get_content("category", pattern="override")`
2. **Collection pattern override** (medium): Defined in collection YAML
3. **Category default patterns** (lowest): Category's configured patterns

**Implementation:**
```python
def resolve_patterns(category: str, explicit_pattern: Optional[str],
                    collection_overrides: Dict[str, List[str]]) -> List[str]:
    if explicit_pattern:
        return [explicit_pattern]  # Tool call wins

    if category in collection_overrides:
        return collection_overrides[category]  # Collection override

    return get_category_default_patterns(category)  # Category default
```

**Rationale:**
- Predictable behavior with clear precedence
- Allows fine-grained control when needed
- Maintains backward compatibility
- Supports both ad-hoc and configured usage patterns

### Common FileInfo Gathering and Rendering Architecture

**Decision**: Extract common FileInfo gathering logic and shared rendering function

**Current Problem:**
- `internal_category_content` returns `Result[str]` (already rendered)
- `get_content` needs `List[FileInfo]` to aggregate across categories
- Cannot reuse `internal_category_content` directly due to return type mismatch
- Rendering logic is duplicated

**New Architecture:**
```python
async def gather_category_fileinfos(
    category_name: str,
    patterns: Optional[List[str]] = None,
    collection_overrides: Optional[Dict[str, List[str]]] = None
) -> List[FileInfo]:
    """Common function to gather FileInfo for a category"""
    # Handle pattern resolution (call > collection > category defaults)
    # Discover files using resolved patterns
    # Return FileInfo objects without rendering

async def render_fileinfos(
    files: List[FileInfo],
    context_name: str
) -> str:
    """Common function to render FileInfo list to content"""
    # Handle template context
    # Read and render file contents
    # Format using formatter
    # Return rendered content string

async def internal_category_content(args: CategoryContentArgs) -> Result[str]:
    """Refactored to use common functions"""
    files = await gather_category_fileinfos(args.category, args.pattern)
    content = await render_fileinfos(files, args.category)
    return Result.ok(content)

async def gather_content(expression: str) -> List[FileInfo]:
    """Process expression and return unified FileInfo list"""
    sub_expressions = split_by_comma(expression)
    all_files = []

    for sub_expr in sub_expressions:
        name, patterns = split_by_first_slash(sub_expr)

        if is_collection(name):
            # Recursive call for collection
            collection_expr = get_collection_expression(name)
            files = await gather_content(collection_expr)
            all_files.extend(files)
        else:
            # Use common FileInfo gathering
            files = await gather_category_fileinfos(name, patterns)
            all_files.extend(files)

    return deduplicate_by_path(all_files)

async def get_content(args: ContentArgs) -> Result[str]:
    """Main entry point using common functions"""
    files = await gather_content(args.category_or_collection)
    content = await render_fileinfos(files, args.category_or_collection)
    return Result.ok(content)
```

**Benefits:**
- **Shared FileInfo logic**: Both tools use same category file gathering
- **Shared rendering**: Both tools use same content formatting
- **No duplication**: Common functions eliminate code duplication
- **Consistent behavior**: Same logic guarantees same results
- **Clean separation**: FileInfo gathering vs content rendering

**Decision**: Implement gather_content function that delegates to existing internal tools rather than duplicating logic

**Current Problem:**
- `get_content` duplicates category content logic
- No reuse of existing `internal_category_content` function
- Inconsistent behavior between direct category access and unified access

**New Architecture:**
```python
async def gather_content(expression: str) -> List[FileInfo]:
    """Process expression and return unified FileInfo list"""
    sub_expressions = split_by_comma(expression)
    all_files = []

    for sub_expr in sub_expressions:
        name, patterns = split_by_first_slash(sub_expr)

        if is_collection(name):
            # Recursive call for collection
            collection_expr = get_collection_expression(name)
            files = await gather_content(collection_expr)
            all_files.extend(files)
        else:
            # Delegate to existing internal tool
            args = CategoryContentArgs(category=name, pattern=patterns)
            result = await internal_category_content(args)
            files = extract_fileinfo_from_result(result)
            all_files.extend(files)

    return deduplicate_by_path(all_files)

async def get_content(args: ContentArgs) -> Result[str]:
    """Main entry point - delegates to gather_content"""
    files = await gather_content(args.category_or_collection)
    content = render_files(files)
    return Result.ok(content)
```

**Benefits:**
- Reuses existing `internal_category_content` logic
- Consistent behavior across all access patterns
- Recursive collection resolution
- Clean separation of concerns
- No code duplication

**FileInfo Flow:**
1. Parse expression into sub-expressions
2. For each sub-expression, determine collection vs category
3. Collections: recursive gather_content call
4. Categories: delegate to internal_category_content
5. Aggregate all FileInfo objects
6. De-duplicate by absolute path
7. Render final content

### DocumentExpression Model Design

**Decision**: Use single DocumentExpression class for both category and collection parsing

**Model Structure:**
```python
@dataclass
class DocumentExpression:
    raw_input: str              # Original user input
    name: str                   # Parsed category or collection name
    patterns: Optional[List[str]] = None  # Parsed patterns if any
```

**Resolution Logic:**
```python
def resolve_expression(expr: DocumentExpression) -> ContentResult:
    # 1. Try as collection first
    if collection_exists(expr.name):
        return resolve_as_collection(expr)

    # 2. Fall back to category
    if category_exists(expr.name):
        return resolve_as_category(expr)

    # 3. Error if neither exists
    return error(f"No collection or category named '{expr.name}'")
```

**Benefits:**
- Single parsing model handles all cases
- Runtime resolution allows flexible naming
- Deferred validation enables lenient parsing
- Clear precedence: collections before categories

### Category Name Validation Strategy

**Decision**: Two-tier validation - lenient parsing, strict creation

**Parsing Rules (Lenient):**
- Allow underscore prefix for system/existing categories
- Allow special characters for expression parsing
- Defer validation until resolution

**Creation Rules (Strict):**
- Disallow underscore prefix (reserved for system)
- Validate against expression syntax conflicts
- Standard identifier validation

**Implementation:**
```python
def validate_for_parsing(name: str) -> bool:
    """Lenient validation for parsing user expressions"""
    return len(name) > 0 and not name.isspace()

def validate_for_creation(name: str) -> bool:
    """Strict validation for user-created categories"""
    if name.startswith('_'):
        raise ValidationError("Underscore prefix reserved for system categories")

    if any(char in name for char in ['+', ',', '/']):
        raise ValidationError("Category name conflicts with expression syntax")

    return is_valid_identifier(name)
```

**Decision**: Extend Collection to support both simple and override syntax

**Data Model:**
```python
@dataclass
class Collection:
    name: str
    description: Optional[str]
    categories: List[Union[str, Dict[str, List[str]]]]  # Mixed format support
```

**YAML Configuration:**
```yaml
collections:
  mixed-example:
    description: "Demonstrates both syntaxes"
    categories:
      - api-reference                           # Simple: use defaults
      - user-guides: ["getting-started*.md"]   # Override: specific patterns
      - tutorials                               # Simple: use defaults
```

**Serialization Logic:**
- Simple category: stored as string
- Category with override: stored as single-key dict `{category: [patterns]}`
- Deserialization handles both formats transparently

**Rationale:**
- Backward compatible with existing collections
- Flexible configuration without verbosity
- Clear distinction between default and override usage
- Extensible for future collection enhancements

### Result Handling Consistency

**Decision**: Treat "no content found" as successful operation with advisory message

**Current Problem:**
- Different tools handle empty results inconsistently
- Some return errors, others return empty content
- Users can't distinguish between "no matches" and "actual error"

**New Approach:**
```python
# Before: Inconsistent error handling
Result.failure("No matching content found")  # Treated as error

# After: Consistent success with advisory
Result.ok("", message="No content found for pattern 'xyz'")  # Success with info
```

**Benefits:**
- Consistent UX across all content retrieval scenarios
- Clear distinction between operational errors and empty results
- Better composability for complex expressions
- Informative messages without error noise

### Expression Parser Architecture

**Decision**: Lightweight recursive descent parser with clear error reporting

**Parser Structure:**
```python
class ExpressionParser:
    def parse_expression(self, expr: str) -> List[CategoryPattern]:
        """Parse comma-separated category expressions"""

    def parse_category_pattern(self, part: str) -> CategoryPattern:
        """Parse single category/pattern expression"""

    def parse_patterns(self, pattern_str: str) -> List[str]:
        """Parse plus-separated pattern list"""
```

**Error Handling:**
- Precise error locations with character positions
- Clear error messages with suggestions
- Graceful degradation for partial failures
- Validation at parse time, not execution time

**Rationale:**
- Simple implementation for well-defined grammar
- Excellent error reporting for user experience
- Extensible for future syntax enhancements
- Minimal dependencies and complexity

### Tool Consolidation Strategy

**Decision**: Gradual deprecation with clear migration path

**Phase 1-3**: Additive enhancements
- All existing tools continue working unchanged
- New syntax available as enhancement
- No breaking changes or deprecation warnings

**Phase 4-5**: Deprecation and migration
- `get_collection_content` marked as deprecated
- Deprecation warnings with migration examples
- Documentation updated to recommend `get_content`
- All functionality available through unified tool

**Future**: Clean removal
- `get_collection_content` removed in next major version
- Single unified content access pattern
- Simplified API surface

**Migration Examples:**
```python
# Old syntax (deprecated but working)
get_collection_content(collection="docs")

# New syntax (recommended)
get_content("docs")

# Enhanced capabilities (only available in new syntax)
get_content("docs/api+tutorial,lang/python")
```

## Implementation Strategy

### Phase-Based Rollout

**Phase 1: Foundation**
- Implement slash syntax parsing
- Fix Result.ok() method signature
- Establish consistent error handling patterns
- No user-visible changes to existing functionality

**Phase 2: Multi-Pattern**
- Add `+` separator support within categories
- Extend pattern matching for multiple patterns
- Maintain backward compatibility with single patterns

**Phase 3: Expression Support**
- Implement comma-separated multi-category expressions
- Add expression parser with proper error handling
- Support complex nested expressions

**Phase 4: Collection Enhancement**
- Extend Collection model for pattern overrides
- Implement three-tier pattern resolution
- Update collection management tools

**Phase 5: Consolidation**
- Migrate collection functionality to `get_content`
- Deprecate `get_collection_content` with migration guidance
- Finalize unified API

### Backward Compatibility Strategy

**Existing Code Protection:**
- All current `get_content(category, pattern)` calls continue working
- All current `get_collection_content(collection="name")` calls continue working
- All existing collection configurations remain valid
- No changes to existing tool signatures during transition

**Migration Support:**
- Clear documentation for new syntax
- Side-by-side examples showing old vs new approaches
- Automated migration suggestions where possible
- Gradual deprecation timeline with advance notice

### Testing Strategy

**Unit Testing:**
- Expression parser with comprehensive edge cases
- Pattern resolution logic with all priority combinations
- Collection model serialization/deserialization
- Error handling and validation

**Integration Testing:**
- End-to-end content retrieval scenarios
- Mixed old/new syntax usage
- Complex expression combinations
- Performance comparison with existing tools

**Backward Compatibility Testing:**
- Existing code continues working unchanged
- Legacy collections work with new features
- Migration scenarios work as documented

## Risks / Trade-offs

### Complexity Risk
- **Risk**: Expression syntax might be too complex for simple use cases
- **Mitigation**: Simple cases remain simple (`get_content("category")`)
- **Mitigation**: Progressive disclosure - advanced features optional

### Performance Risk
- **Risk**: Expression parsing might slow down simple operations
- **Mitigation**: Optimize parser for common cases
- **Mitigation**: Cache parsed expressions where appropriate
- **Mitigation**: Benchmark against existing performance

### Migration Risk
- **Risk**: Users might be confused by multiple ways to do same thing
- **Mitigation**: Clear documentation with recommended approaches
- **Mitigation**: Gradual deprecation with plenty of notice
- **Mitigation**: Migration examples and tooling

### Parsing Ambiguity Risk
- **Risk**: Edge cases in expression syntax might be ambiguous
- **Mitigation**: Comprehensive test suite for edge cases
- **Mitigation**: Clear error messages for ambiguous input
- **Mitigation**: Conservative parsing with explicit error handling

## Migration Plan

### Immediate (Phases 1-3)
- Roll out new syntax as additive enhancement
- Update documentation with examples
- No changes to existing code required

### Short-term (Phase 4)
- Introduce collection pattern overrides
- Update collection management tools
- Provide migration examples for advanced use cases

### Medium-term (Phase 5)
- Mark `get_collection_content` as deprecated
- Provide clear migration path and examples
- Update all internal usage to new syntax

### Long-term
- Remove deprecated tools in next major version
- Establish unified content access as standard pattern
- Clean up API surface area

## Open Questions

1. **Performance**: Should we implement expression result caching for repeated queries?
2. **Validation**: Should pattern overrides be validated against actual file system at configuration time?
3. **Extensions**: Should we support pattern exclusions (e.g., `*.py+!test_*.py`)?
4. **Escaping**: Do we need escape sequences for literal `+` and `,` characters in patterns?

## Success Metrics

- **Backward Compatibility**: 100% of existing code continues working
- **Performance**: New implementation performs within 10% of existing tools
- **Adoption**: Documentation examples primarily use new syntax
- **User Experience**: Reduced support questions about content retrieval
- **API Simplification**: Single tool handles 90%+ of content access scenarios
