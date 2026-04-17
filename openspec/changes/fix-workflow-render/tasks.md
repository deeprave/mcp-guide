## 1. Flag display formatting

- [x] 1.1 Identify the display-oriented flag projections used by project/workflow templates
- [x] 1.2 Integrate the canonical `FeatureValue` display formatting path into the relevant display-oriented flag projections
- [x] 1.3 Apply that display formatting when building `project.project_flag_values`
- [x] 1.4 Ensure boolean workflow values continue to render correctly for display without changing raw structured flag access elsewhere

## 2. Template update

- [x] 2.1 Update the affected project/workflow template or partial only as needed to align with the formatted flag value output
- [x] 2.2 Verify the rendered output for custom workflow lists matches the intended plain phase-name representation
- [x] 2.3 Verify dict-like flags such as `workflow-consent` render sensibly in project output
- [x] 2.4 Verify the raw flag dictionaries remain unchanged for non-display consumers

## 3. Tests

- [x] 3.1 Add or update rendering tests covering custom workflow list display
- [x] 3.2 Add or update tests covering dict/nested flag display formatting
- [x] 3.3 Add or update tests proving generic `IndexedList` rendering semantics are unchanged
- [x] 3.4 Add or update tests proving raw structured flag dictionaries remain available separately from display-oriented projections

## 4. Validation

- [x] 4.1 Run the focused rendering/template tests for the touched behavior
- [x] 4.2 Run `openspec validate fix-workflow-render --strict`
