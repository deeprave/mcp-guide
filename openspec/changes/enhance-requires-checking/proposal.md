# Enhance requires-* Frontmatter Checking

**Status**: Proposed
**Priority**: High
**Complexity**: Medium
**Related**: unify-template-rendering (parent change)

## Why

The current `render_template()` implementation only performs simple truthy checks for `requires-*` directives, which is insufficient for complex requirements like phase-specific workflow checks. The legacy `check_frontmatter_requirements()` function supports list and exact-match checking, but will become unused once all template handling is migrated to the unified API.

Without enhanced checking:
- Commands cannot specify phase-specific requirements (e.g., `requires-workflow: [discussion, planning]`)
- Cannot check for specific feature configurations (e.g., `requires-workflow: implementation=true`)
- Loss of functionality compared to legacy system
- Inconsistent behavior between old and new rendering paths

## What Changes

### Core Enhancement
- Enhance `render_template()` to support sophisticated `requires-*` checking:
  - **Boolean**: `requires-feature: true` → check if feature is truthy
  - **List membership**: `requires-feature: [value1, value2]` → check if feature value is in list OR if feature is list/dict containing all specified elements
  - **Key-value pairs**: `requires-feature: [key=value, key2=value2]` → check if feature is dict with matching key-value pairs

### Workflow Simplification
- Redesign workflow flag structure to support three formats:
  1. **Simple list**: `workflow: [discussion, planning, implementation, check, review]` - no consent required
  2. **Dict with consent**: `workflow: {discussion: false, planning: false, implementation: true, check: false, review: true}` - explicit consent markers
  3. **Boolean shorthand**: `workflow: true` - expands to default dict with consent markers

- Update flag validation to translate `workflow: true` → default dict structure
- Remove `*` prefix/suffix consent markers in favor of boolean consent values
- Support generic checking: `requires-workflow: [discussion, implementation]` checks keys exist
- Support consent checking: `requires-workflow: implementation=true` checks consent is true

### Generic Implementation
- No special-casing of "workflow" - all flags support list/dict checking
- Flag validation handles boolean → default value expansion
- Consistent behavior across all `requires-*` directives

## Technical Approach

### 1. Enhanced Requires Checking Algorithm

```python
def check_requires_directive(
    required_value: Any,
    actual_value: Any
) -> bool:
    """Check if requirement is satisfied."""

    # Boolean: simple truthy check
    if isinstance(required_value, bool):
        return bool(actual_value) == required_value

    # List: membership or containment check
    if isinstance(required_value, list):
        # Check for key=value pairs
        if any('=' in str(item) for item in required_value):
            # Parse key=value pairs
            pairs = parse_key_value_pairs(required_value)
            if not isinstance(actual_value, dict):
                return False
            return all(actual_value.get(k) == v for k, v in pairs.items())

        # List membership: actual_value in required_value
        if not isinstance(actual_value, (list, dict)):
            return actual_value in required_value

        # Containment: all required items in actual_value
        if isinstance(actual_value, list):
            return all(item in actual_value for item in required_value)
        if isinstance(actual_value, dict):
            return all(key in actual_value for key in required_value)

    # Exact match
    return actual_value == required_value
```

### 2. Workflow Flag Structure

**Current**:
```yaml
workflow:
  file: .guide.yaml
  phases: [discussion, planning, implementation*, check, review]
  transitions:
    default: discussion
```

**Proposed**:
```yaml
# Option 1: Simple list (no consent)
workflow: [discussion, planning, implementation, check, review]

# Option 2: Dict with consent markers
workflow:
  discussion: false
  planning: false
  implementation: true  # consent given
  check: false
  review: true  # consent given

# Option 3: Boolean shorthand
workflow: true  # expands to default dict
```

### 3. Flag Validation Enhancement

Add validation logic to expand `workflow: true`:
```python
def validate_workflow_flag(value: FeatureValue) -> FeatureValue:
    """Validate and expand workflow flag."""
    if value is True:
        # Expand to default dict with consent markers
        return {
            "discussion": False,
            "planning": False,
            "implementation": True,
            "check": False,
            "review": True,
        }
    return value
```

## Success Criteria

1. `requires-workflow: [discussion, planning]` correctly filters templates based on current phase
2. `requires-workflow: implementation=true` checks both phase and consent
3. `workflow: true` expands to default dict structure
4. All existing `requires-*` directives continue to work
5. Generic implementation works for any flag type
6. Legacy `check_frontmatter_requirements()` can be removed
7. All tests pass with new checking logic

## Migration Impact

- **Breaking**: Workflow flag structure changes (but with backward compatibility via validation)
- **Non-breaking**: Enhanced `requires-*` checking is additive
- **Deprecation**: `check_frontmatter_requirements()` becomes unused and can be removed
- **Templates**: Workflow commands may need frontmatter updates to use new format

## Dependencies

- Requires completed `unify-template-rendering` core implementation
- Requires completed `migrate-command-rendering` subspec
- May require updates to workflow command templates
