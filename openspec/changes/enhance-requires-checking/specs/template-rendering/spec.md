# Template Rendering Spec Delta

## MODIFIED Requirements

### Requirement: Frontmatter Requirements Checking

The template rendering system SHALL support sophisticated `requires-*` directive checking.

The system SHALL support two checking modes:

1. **Boolean Mode**: When `requires-<flag>: true|false`, check if flag value is truthy/falsy
2. **List Membership Mode**: When `requires-<flag>: [value1, value2]`, check if ANY value matches (OR logic):
   - If flag value is scalar: value must be in the list
   - If flag value is list: ANY required value must be present in flag list
   - If flag value is dict: ANY required key must be present in flag dict

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

#### Scenario: List Membership with List Value (ANY match)

- GIVEN a template with `requires-workflow: [discussion, implementation]`
- WHEN workflow flag is `[discussion, planning, implementation, check, review]`
- THEN template is included (discussion is present)
- WHEN workflow flag is `[planning, check, review]`
- THEN template is filtered out (neither discussion nor implementation present)

#### Scenario: List Membership with Dict Value (ANY key)

- GIVEN a template with `requires-config: [feature1, feature2]`
- WHEN config flag is `{feature1: true, feature3: false}`
- THEN template is included (feature1 key exists)
- WHEN config flag is `{feature3: true, feature4: false}`
- THEN template is filtered out (neither feature1 nor feature2 keys exist)

#### Scenario: Multiple Requirements

- GIVEN a template with `requires-workflow: [implementation]` AND `requires-openspec: true`
- WHEN workflow contains "implementation" AND openspec is truthy
- THEN template is included
- WHEN either requirement is not met
- THEN template is filtered out

## ADDED Requirements

### Requirement: Workflow Flag Structure

The system SHALL support two workflow flag formats:

1. **Boolean Shorthand**: `workflow: true` - expands to default phase list
2. **Simple List**: `workflow: [phase1, phase2, ...]` - explicit phase list

The system SHALL validate and expand `workflow: true` to the default phase list during flag resolution.

The default phase list SHALL be:
```yaml
workflow: [discussion, planning, implementation, check, review]
```

#### Scenario: Boolean Shorthand Expansion

- GIVEN workflow flag is set to `true`
- WHEN flag is validated
- THEN flag is expanded to `[discussion, planning, implementation, check, review]`
- WHEN checking `requires-workflow: [implementation]`
- THEN requirement is satisfied (implementation is in list)

#### Scenario: Simple List Format

- GIVEN workflow flag is `[discussion, planning, implementation, check, review]`
- WHEN checking `requires-workflow: [discussion]`
- THEN requirement is satisfied (discussion is in list)
- WHEN checking `requires-workflow: [deployment]`
- THEN requirement is NOT satisfied (deployment not in list)

### Requirement: Workflow Consent Configuration

The system SHALL support a separate `workflow-consent` flag for transition consent requirements.

The system SHALL support three workflow-consent formats:

1. **Boolean Shorthand**: `workflow-consent: true` or not set - expands to default consent
2. **Explicit Disable**: `workflow-consent: false` - no consent requirements
3. **Custom Consent**: Dict mapping phase names to consent types

The default consent configuration SHALL be:
```yaml
workflow-consent:
  implementation: [entry]
  review: [exit]
```

Consent types SHALL be:
- `entry`: Consent required before entering phase
- `exit`: Consent required before exiting phase

#### Scenario: Default Consent

- GIVEN workflow is enabled
- AND workflow-consent is not set OR set to `true`
- WHEN building workflow.transitions
- THEN implementation has `pre: true`
- AND review has `post: true`
- AND other phases have `pre: false, post: false`

#### Scenario: No Consent

- GIVEN workflow is enabled
- AND workflow-consent is `false`
- WHEN building workflow.transitions
- THEN all phases have `pre: false, post: false`

#### Scenario: Custom Consent

- GIVEN workflow-consent is `{planning: [entry], check: [exit]}`
- WHEN building workflow.transitions
- THEN planning has `pre: true, post: false`
- AND check has `pre: false, post: true`
- AND other phases have `pre: false, post: false`

### Requirement: Workflow Context Building

The system SHALL build `workflow.transitions` from both `workflow` and `workflow-consent` flags.

The system SHALL remove `*` marker parsing from phase names.

The system SHALL maintain phase ordering from the workflow list.

#### Scenario: Transitions from Separate Flags

- GIVEN workflow is `[discussion, planning, implementation, check, review]`
- AND workflow-consent is default (implementation entry, review exit)
- WHEN building workflow.transitions
- THEN transitions contains all phases with correct pre/post values
- AND transitions.default is "discussion"
- AND phase ordering is preserved for "next phase" logic

## REMOVED Requirements

### Requirement: Marker-Based Consent

The `*` prefix/suffix markers for consent SHALL be removed.

Phase names in workflow flag SHALL NOT contain `*` markers.

Consent SHALL be configured via separate `workflow-consent` flag.

#### Scenario: No Markers in Phase Names

- GIVEN workflow flag is validated
- WHEN workflow contains phase names
- THEN phase names do NOT contain `*` prefix or suffix
- AND clean phase names are used directly

### Requirement: Legacy Requirements Checking

The `check_frontmatter_requirements()` function SHALL be removed.

All requirements checking SHALL use the enhanced checking in `render_template()`.

#### Scenario: Migration Complete

- GIVEN all template rendering uses `render_template()` API
- WHEN searching for `check_frontmatter_requirements` usage
- THEN no usages are found
- AND function is removed from codebase
