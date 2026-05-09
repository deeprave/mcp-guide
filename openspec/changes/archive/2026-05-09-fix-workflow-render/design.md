# Design: Fix Workflow Render

## Summary

The rendering system wraps all lists in `IndexedList` so Mustache templates can
iterate with `first` and `last` metadata. That behavior is correct and must not
be changed.

The bug arises because display-oriented flag lists such as
`project.project_flag_values` still allow templates to render values through
the generic wrapped representation. When a template wants to display one of
those values directly, the iterable wrapper form is not suitable for user-facing
output.

## Approach

Use the canonical `FeatureValue` display formatting path introduced by the
feature-value refactor while preserving the existing iterable workflow
structure and the raw underlying flag values.

Recommended shape:

- keep the existing raw flag structures used for rendering logic and
  conditional behavior
- format display-oriented flag projections before they reach templates
- keep `project.project_flag_values` as a display-oriented list of
  `{key, value}` pairs, but make `value` the rendered display string
- rely on the shared `FeatureValue` display behavior for booleans, lists,
  dicts, and nested combinations rather than adding new formatting logic in
  the render layer

The preferred implementation is the smallest change that fixes the current
project template rendering without changing generic list semantics.

## Constraints

- `IndexedList` semantics must remain unchanged globally
- no changes to generic list conversion behavior
- display formatting should be centralized in the canonical flag model, not
  duplicated in Mustache or reimplemented in the render layer
- templates using `project.project_flag_values` should continue to read
  `{{value}}` and receive already-formatted display text

## Validation

Tests should cover:

- boolean workflow shorthand behavior remains unchanged
- direct project flag display uses plain phase names for custom workflow lists
- structured dict-like flags such as `workflow-consent` render as stable
  user-facing strings
- raw structured flag dictionaries remain available separately for templates
  that need non-display access
- generic list rendering behavior outside workflow context remains unchanged
