# Design: Fix Workflow Render

## Summary

The rendering system wraps all lists in `IndexedList` so Mustache templates can
iterate with `first` and `last` metadata. That behavior is correct and must not
be changed.

The bug arises because display-oriented flag lists such as
`project.project_flag_values` currently carry raw values. When a template wants
to display one of those values directly, the generic wrapped representation is
not suitable for user-facing output.

## Approach

Add a shared flag-value display formatter while preserving the existing iterable
workflow structure and the raw underlying flag values.

Recommended shape:

- keep the existing raw flag structures used for rendering logic and
  conditional behavior
- format display-oriented flag projections before they reach templates
- keep `project.project_flag_values` as a display-oriented list of
  `{key, value}` pairs, but make `value` the rendered display string

Formatter responsibilities:

- render booleans consistently
- render scalar lists as compact list strings
- render dicts and nested dict/list combinations recursively
- render workflow and workflow-consent values correctly without introducing
  workflow-only special cases in Mustache templates

The preferred implementation is the smallest change that fixes the current
project template rendering without changing generic list semantics.

## Constraints

- `IndexedList` semantics must remain unchanged globally
- no changes to generic list conversion behavior
- display formatting should be centralized in code, not duplicated in Mustache
- templates using `project.project_flag_values` should continue to read
  `{{value}}` and receive already-formatted display text

## Validation

Tests should cover:

- boolean workflow shorthand behavior remains unchanged
- direct project flag display uses plain phase names for custom workflow lists
- structured dict-like flags such as `workflow-consent` render as stable
  user-facing strings
- generic list rendering behavior outside workflow context remains unchanged
