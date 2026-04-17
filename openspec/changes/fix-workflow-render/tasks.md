## 1. Flag display formatting

- [ ] 1.1 Identify the display-oriented flag projections used by project/workflow templates
- [ ] 1.2 Add a shared flag-value formatter for booleans, scalars, lists, dicts, and nested combinations
- [ ] 1.3 Apply that formatter when building `project.project_flag_values`
- [ ] 1.4 Ensure boolean workflow values continue to render correctly for display

## 2. Template update

- [ ] 2.1 Update the affected project/workflow template or partial only as needed to align with the formatted flag value output
- [ ] 2.2 Verify the rendered output for custom workflow lists matches the intended plain phase-name representation
- [ ] 2.3 Verify dict-like flags such as `workflow-consent` render sensibly in project output

## 3. Tests

- [ ] 3.1 Add or update rendering tests covering custom workflow list display
- [ ] 3.2 Add or update tests covering dict/nested flag display formatting
- [ ] 3.3 Add or update tests proving generic `IndexedList` rendering semantics are unchanged

## 4. Validation

- [ ] 4.1 Run the focused rendering/template tests for the touched behavior
- [ ] 4.2 Run `openspec validate fix-workflow-render --strict`
