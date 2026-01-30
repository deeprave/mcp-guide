# Template Rendering Spec Delta

## MODIFIED Requirements

### Requirement: Frontmatter Requirements Checking

The template rendering system SHALL support sophisticated `requires-*` directive checking.

The system SHALL support three checking modes:

1. **Boolean Mode**: When `requires-<flag>: true|false`, check if flag value is truthy/falsy
2. **List Membership Mode**: When `requires-<flag>: [value1, value2]`, check:
   - If flag value is scalar: value must be in the list
   - If flag value is list: all required values must be present in flag list
   - If flag value is dict: all required keys must be present in flag dict
3. **Key-Value Mode**: When `requires-<flag>: [key=value, key2=value2]`, check:
   - Flag value must be a dict
   - All specified key-value pairs must match

The system SHALL apply checking generically to all `requires-*` directives without special-casing specific flags.

#### Scenario: Boolean Requirement

- GIVEN a template with `requires-workflow: true`
- WHEN workflow flag is set to any truthy value
- THEN template is included
- WHEN workflow flag is false or missing
- THEN template is filtered out

#### Scenario: List Membership with Scalar Value

- GIVEN a template with `requires-phase: [discussion, planning]`
- WHEN phase flag is set to "discussion"
- THEN template is included
- WHEN phase flag is set to "implementation"
- THEN template is filtered out

#### Scenario: List Containment with List Value

- GIVEN a template with `requires-workflow: [discussion, implementation]`
- WHEN workflow flag is `[discussion, planning, implementation, check, review]`
- THEN template is included (both required phases present)
- WHEN workflow flag is `[discussion, planning]`
- THEN template is filtered out (implementation missing)

#### Scenario: List Containment with Dict Value

- GIVEN a template with `requires-workflow: [discussion, implementation]`
- WHEN workflow flag is `{discussion: false, planning: false, implementation: true, check: false, review: true}`
- THEN template is included (both required keys present)
- WHEN workflow flag is `{discussion: false, planning: false}`
- THEN template is filtered out (implementation key missing)

#### Scenario: Key-Value Pair Checking

- GIVEN a template with `requires-workflow: [implementation=true, check=true]`
- WHEN workflow flag is `{discussion: false, planning: false, implementation: true, check: true, review: false}`
- THEN template is included (both key-value pairs match)
- WHEN workflow flag is `{discussion: false, planning: false, implementation: false, check: true, review: false}`
- THEN template is filtered out (implementation is false, not true)

#### Scenario: Multiple Requirements

- GIVEN a template with `requires-workflow: [implementation]` AND `requires-openspec: true`
- WHEN workflow contains "implementation" AND openspec is truthy
- THEN template is included
- WHEN either requirement is not met
- THEN template is filtered out

## ADDED Requirements

### Requirement: Workflow Flag Structure

The system SHALL support three workflow flag formats:

1. **Simple List**: `workflow: [phase1, phase2, ...]` - list of valid phases, no consent required
2. **Dict with Consent**: `workflow: {phase1: bool, phase2: bool, ...}` - phases with consent markers
3. **Boolean Shorthand**: `workflow: true` - expands to default dict structure

The system SHALL validate and expand `workflow: true` to the default dict structure during flag resolution.

The default dict structure SHALL be:
```yaml
workflow:
  discussion: false
  planning: false
  implementation: true
  check: false
  review: true
```

#### Scenario: Simple List Format

- GIVEN workflow flag is `[discussion, planning, implementation, check, review]`
- WHEN checking `requires-workflow: [discussion]`
- THEN requirement is satisfied (discussion is in list)
- WHEN checking `requires-workflow: discussion=true`
- THEN requirement is NOT satisfied (not a dict, cannot check consent)

#### Scenario: Dict with Consent Format

- GIVEN workflow flag is `{discussion: false, planning: false, implementation: true, check: false, review: true}`
- WHEN checking `requires-workflow: [implementation]`
- THEN requirement is satisfied (implementation key exists)
- WHEN checking `requires-workflow: implementation=true`
- THEN requirement is satisfied (implementation consent is true)
- WHEN checking `requires-workflow: discussion=true`
- THEN requirement is NOT satisfied (discussion consent is false)

#### Scenario: Boolean Shorthand Expansion

- GIVEN workflow flag is set to `true`
- WHEN flag is validated
- THEN flag is expanded to default dict structure
- WHEN checking `requires-workflow: implementation=true`
- THEN requirement is satisfied (default has implementation: true)

### Requirement: Generic Flag Validation

The system SHALL provide a validation mechanism for flags that need expansion or transformation.

The system SHALL support flag-specific validators that can transform flag values during resolution.

The workflow flag validator SHALL expand `true` to the default dict structure.

Other flags MAY implement similar expansion logic as needed.

#### Scenario: Workflow Flag Validation

- GIVEN workflow flag is set to `true` in configuration
- WHEN flags are resolved
- THEN workflow validator is called
- AND workflow flag is expanded to default dict
- AND expanded value is used for requirements checking

## REMOVED Requirements

### Requirement: Legacy Requirements Checking

The `check_frontmatter_requirements()` function is REMOVED.

All requirements checking SHALL use the enhanced checking in `render_template()`.

#### Scenario: Migration Complete

- GIVEN all template rendering uses `render_template()` API
- WHEN searching for `check_frontmatter_requirements` usage
- THEN no usages are found
- AND function is removed from codebase
