# Fix Workflow Render

## Why

Structured project flag values currently render poorly in project templates
because display-oriented flag lists still expose values in a form that lets
Mustache render the generic `IndexedList` iterator shape instead of a
user-friendly value. For workflow lists this can produce output like:

```yaml
workflow: [discussion, implementation, check, review]
```

can render in templates as:

```text
workflow: [{'value': 'discussion', 'first': True, 'last': False}, ...]
```

instead of the intended user-facing display:

```text
workflow: ['discussion', 'implementation', 'check', 'review']
```

This is not a bug in generic list conversion. The existing `IndexedList`
behavior is intentional and must remain unchanged for template iteration
semantics across the rendering system.

The recently completed `FeatureValue` refactor now provides a canonical runtime
flag model and central display formatting path. This change should build on
that work rather than introduce a parallel workflow-specific formatter.

## What Changes

1. Use the canonical `FeatureValue` display formatting path when building
   display-oriented flag projections such as `project.project_flag_values`.
2. Ensure the project rendering template continues to use `{{value}}`, with
   that field containing the formatted display string for structured flags.
3. Keep generic list rendering and `IndexedList` behavior unchanged.
4. Do not change the raw structured flag dictionaries exposed elsewhere in the
   template context.

## Impact

- Affected specs:
  - `template-rendering`
- Affected code:
  - flag display integration in `src/mcp_guide/render/`
  - project/workflow templates or partials under `src/mcp_guide/templates/`
- Breaking changes: None
