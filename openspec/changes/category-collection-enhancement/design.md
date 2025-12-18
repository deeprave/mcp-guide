# Category Collection Enhancement Design

## Context

This change enhances the category and collection system to provide better content retrieval and error handling.

## Goals / Non-Goals

- Goals: Improve content retrieval consistency, better error handling, unified content access
- Non-Goals: Breaking existing API compatibility

## Decisions

### Result.ok() Method Signature Fix

**Decision**: Make `value` parameter optional in `Result.ok()` to match class design

**Current Issue:**
- `Result` class has `value: Optional[T] = None` (optional field)
- `Result.ok()` method requires `value: T` (mandatory parameter)
- This creates inconsistency and forces awkward empty string usage

**Fix:**
```python
# Current (inconsistent)
def ok(cls, value: T, message: Optional[str] = None, instruction: Optional[str] = None)

# Fixed (consistent)
def ok(cls, value: Optional[T] = None, message: Optional[str] = None, instruction: Optional[str] = None)
```

**Usage Impact:**
```python
# Before: forced to provide empty value
Result.ok("", message="No content found")

# After: clean optional value
Result.ok(message="No content found")
```

### Content Retrieval Result Handling

**Decision**: Treat "no content found" as successful operation, not an error

**Current Behavior:**
- `Result.failure("No matching content found")` - treated as an error
- Shows error messages to users
- Inconsistent with collection behavior where some categories might not match patterns

**New Behavior:**
- `Result.ok("", message="No content found")` - successful operation with advisory message
- Returns blank content with informative message
- Consistent across all content retrieval scenarios

**Rationale:**
- Not finding content is a valid outcome, not a failure condition
- Provides cleaner UX - advisory messages instead of error messages
- Aligns with collection behavior where partial matches are expected
- Enables better composition of content retrieval operations

**Implementation Impact:**
- Modify content retrieval functions to return `Result.ok()` with advisory messages
- Update prompt handlers to display advisory messages appropriately
- Ensure consistent behavior across categories, collections, and unified content access

### Content Path Parsing Enhancement

**Decision**: Support category/pattern syntax in content access functions

**Current Limitation:**
- `get_content("checks/python")` fails because it treats entire string as category name
- Users must use separate parameters: `get_content("checks", "python")`
- No support for comma-separated patterns

**New Behavior:**
```python
# Category/pattern parsing (first / is delimiter)
get_content("checks/python")           # → category="checks", pattern="python"
get_content("checks/python/advanced")  # → category="checks", pattern="python/advanced"

# Multiple patterns in same category (+ separator)
get_content("lang/python+java")        # → category="lang", pattern="python+java"

# Multiple category/pattern pairs (, separator)
get_content("lang/python,guidelines,context/openspec")
# → Equivalent to:
#   get_content("lang", "python") +
#   get_content("guidelines", None) +
#   get_content("context", "openspec")

# Combined syntax
get_content("lang/python+java,guidelines,context/openspec+tutorial")
# → Equivalent to:
#   get_content("lang", "python+java") +
#   get_content("guidelines", None) +
#   get_content("context", "openspec+tutorial")
```

**Implementation:**
- Parse `category_or_collection` parameter in `internal_get_content`
- Split on first `/` if present: `category, pattern = input.split('/', 1)`
- Override explicit pattern parameter if parsing extracts pattern
- Maintain backward compatibility with existing separate parameter usage

**Parsing Rules:**
1. **No `/`**: Use entire string as category/collection name
2. **Contains `/`**: Split on first `/` only
   - Before first `/` → category/collection name
   - After first `/` → pattern (may contain additional `/` characters)
3. **Comma (`,`) support**: Multiple category/pattern pairs
4. **Plus (`+`) support**: Multiple patterns within same category

**Parsing Hierarchy:**
1. **Comma (`,`)**: Separates different category/pattern pairs
2. **Slash (`/`)**: Separates category from pattern(s) within each pair
3. **Plus (`+`)**: Separates multiple patterns within same category

**Examples:**
```python
get_content("checks")                    # category="checks", pattern=None
get_content("checks/python")             # category="checks", pattern="python"
get_content("lang/python+java")          # category="lang", pattern="python+java"
get_content("lang/python,guidelines")    # lang/python + guidelines
get_content("docs/api/v1/auth")          # category="docs", pattern="api/v1/auth"
get_content("lang/python+java,context/openspec+tutorial,guidelines")
# → lang/(python+java) + context/(openspec+tutorial) + guidelines
```

**Backward Compatibility:**
- Existing `get_content(category, pattern)` usage unchanged
- New syntax is additive enhancement
- No breaking changes to current API

## Risks / Trade-offs

- Risk: Existing code expecting failure results may need updates
- Mitigation: Review all callers of content retrieval functions

## Migration Plan

1. Update content retrieval functions to use `Result.ok()` for no content scenarios
2. Update prompt and tool handlers to handle advisory messages
3. Test all content access paths to ensure consistent behavior

## Open Questions

- Should advisory messages be configurable or standardized?
- How should multiple advisory messages be handled in collection scenarios?
