# Enhance requires-* Frontmatter Checking

**Status**: Proposed
**Priority**: High
**Complexity**: Medium
**Related**: unify-template-rendering (parent change)

## Why

The current `render_template()` implementation only performs simple truthy checks for `requires-*` directives, which is insufficient for complex requirements like phase-specific workflow checks. The legacy `check_frontmatter_requirements()` function supports list and exact-match checking, but will become unused once all template handling is migrated to the unified API.

Without enhanced checking:
- Commands cannot specify phase-specific requirements (e.g., `requires-workflow: [discussion, planning]`)
- Loss of functionality compared to legacy system
- Inconsistent behavior between old and new rendering paths

## What Changes

### Core Enhancement
- Enhance `render_template()` to support sophisticated `requires-*` checking:
  - **Boolean**: `requires-feature: true` → check if feature is truthy
  - **List membership**: `requires-feature: [value1, value2]` → check if ANY value matches (OR logic)
    - Scalar actual value: check if actual is in required list
    - List actual value: check if ANY required value is in actual list
    - Dict actual value: check if ANY required key exists in actual dict

### Workflow Simplification
- Simplify workflow flag to pure phase list
- Separate consent requirements into `workflow-consent` flag
- Remove `*` prefix/suffix consent markers from phase names

**Workflow flag formats**:
1. **Boolean shorthand**: `workflow: true` → expands to `[discussion, planning, implementation, check, review]`
2. **Simple list**: `workflow: [discussion, planning, implementation, check, review]`

**Workflow consent formats**:
1. **Boolean shorthand**: `workflow-consent: true` → expands to default consent requirements
2. **Explicit consent**: `workflow-consent: false` → no consent requirements
3. **Custom consent**: 
   ```yaml
   workflow-consent:
     implementation: [entry]
     review: [exit]
   ```

**Default consent** (when `workflow-consent: true` or not set):
```python
DEFAULT_WORKFLOW_CONSENT = {
    "implementation": ["entry"],
    "review": ["exit"],
}
```

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

    # List: membership check (ANY match - OR logic)
    if isinstance(required_value, list):
        # Scalar: check if actual is in required list
        if not isinstance(actual_value, (list, dict)):
            return actual_value in required_value

        # List: check if ANY required value is in actual list
        if isinstance(actual_value, list):
            return any(item in actual_value for item in required_value)
        
        # Dict: check if ANY required key exists in actual dict
        if isinstance(actual_value, dict):
            return any(key in actual_value for key in required_value)

    # Exact match
    return actual_value == required_value
```

### 2. Workflow Flag Structure

**Current**:
```yaml
workflow: [discussion, planning, implementation*, check, review*]
```

**Proposed**:
```yaml
# Boolean shorthand
workflow: true  # expands to [discussion, planning, implementation, check, review]

# Simple list
workflow: [discussion, planning, implementation, check, review]

# Consent configuration (separate flag)
workflow-consent: true  # expands to default consent requirements

# Or explicit consent
workflow-consent:
  implementation: [entry]
  review: [exit]

# Or no consent
workflow-consent: false
```

### 3. Flag Validation Enhancement

```python
# Default phases
DEFAULT_WORKFLOW_PHASES = [
    "discussion",
    "planning", 
    "implementation",
    "check",
    "review",
]

# Default consent requirements
DEFAULT_WORKFLOW_CONSENT = {
    "implementation": ["entry"],
    "review": ["exit"],
}

def validate_workflow_flag(value: FeatureValue) -> FeatureValue:
    """Validate and expand workflow flag."""
    if value is True:
        return DEFAULT_WORKFLOW_PHASES
    # Validate list of phase names
    return value

def validate_workflow_consent_flag(value: FeatureValue) -> FeatureValue:
    """Validate and expand workflow-consent flag."""
    if value is True or value is None:
        return DEFAULT_WORKFLOW_CONSENT
    if value is False:
        return {}
    # Validate dict structure
    return value
```

### 4. Workflow Context Building

Update `WorkflowContextCache._build_workflow_transitions()` to use both flags:

```python
def _build_workflow_transitions(self) -> dict[str, Any]:
    """Build workflow.transitions dict from workflow and workflow-consent flags."""
    
    # Get workflow phases
    workflow_flag = self.task_manager.get_cached_data("workflow_flag")
    if not workflow_flag:
        return {}
    
    # Get consent requirements
    consent_flag = self.task_manager.get_cached_data("workflow_consent_flag")
    if consent_flag is None:
        consent_flag = DEFAULT_WORKFLOW_CONSENT
    
    transitions = {}
    
    for i, phase in enumerate(workflow_flag):
        # First phase is default
        is_default = i == 0
        
        # Check consent requirements for this phase
        consent_config = consent_flag.get(phase, [])
        pre_consent = "entry" in consent_config
        post_consent = "exit" in consent_config
        
        phase_metadata = {
            "pre": pre_consent,
            "post": post_consent,
        }
        
        if is_default:
            phase_metadata["default"] = True
        
        transitions[phase] = phase_metadata
    
    # Add default phase name
    if workflow_flag:
        transitions["default"] = workflow_flag[0]
    
    return transitions
```

## Success Criteria

1. `requires-workflow: [discussion, planning]` correctly filters templates (ANY match)
2. `requires-workflow: true` checks if workflow is enabled
3. `workflow: true` expands to default phase list
4. `workflow-consent: true` expands to default consent requirements
5. `workflow-consent: false` disables all consent requirements
6. All existing `requires-*` directives continue to work
7. Generic implementation works for any flag type
8. Legacy `check_frontmatter_requirements()` can be removed
9. All tests pass with new checking logic

## Migration Impact

- **Breaking**: Workflow flag structure changes from list-with-markers to pure list
  - Remove `*` markers from workflow flag values
  - Add `workflow-consent` flag for consent configuration
- **Non-breaking**: Enhanced `requires-*` checking is additive
- **Cleanup**: `check_frontmatter_requirements()` removed after migration
- **Templates**: No changes needed - `workflow.transitions` still works

## Dependencies

- Requires completed `unify-template-rendering` core implementation
- Requires completed `migrate-command-rendering` subspec
