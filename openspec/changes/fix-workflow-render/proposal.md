# Fix Workflow Render

## Why

Structured project flag values currently render poorly in project templates
because display-oriented flag lists pass raw values straight into Mustache. For
workflow lists this can expose the generic `IndexedList` iterator shape instead
of a user-friendly value. For example, a workflow configured as:

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

## What Changes

1. Add a shared flag-value display formatter that converts booleans, lists,
   dicts, and nested combinations into stable user-facing string output.
2. Use that formatter when building display-oriented flag projections such as
   `project.project_flag_values`.
3. Update the project rendering template to continue using `{{value}}`, with
   that field now containing the formatted display string.
4. Keep generic list rendering and `IndexedList` behavior unchanged.

## Impact

- Affected specs:
  - `template-rendering`
- Affected code:
  - flag display formatting in `src/mcp_guide/render/` or adjacent shared
    formatting helpers
  - project/workflow templates or partials under `src/mcp_guide/templates/`
- Breaking changes: None
