# ADR: Passing Template Arguments to Tools

**Status:** Accepted
**Date:** 2026-03-14

## Context

Command templates (`.mustache`) instruct agents to call tools with specific arguments. Some display behaviour — formatting style, verbosity, layout — is best controlled by the command template rather than hardcoded in the tool. We need a generic mechanism to pass display options from templates through tools into rendering templates.

A naive approach would add specific boolean parameters (`formatted`, `verbose`, `table`) to each tool. This creates tight coupling between tool signatures and display concerns, and requires tool changes for every new display option.

## Decision

Tools that render formatted output accept an `options` parameter of type `list[str]`. Each entry is either:

- A **flag** (truthy): `"verbose"` → `{"verbose": True}`
- A **key=value pair**: `"limit=10"` → `{"limit": "10"}`

The tool converts the list into a dict and merges it into the template context:

```python
options: list[str] = Field(
    default_factory=list,
    description="Display options passed to template.",
)

# Conversion
option_flags: dict[str, str | bool] = {}
for opt in args.options:
    if "=" in opt:
        key, value = opt.split("=", 1)
        option_flags[key] = value
    else:
        option_flags[opt] = True
```

Templates use standard Mustache conditionals:

```mustache
{{#verbose}}
  - Exported: {{exported_at}}
{{/verbose}}
{{#limit}}
  Showing first {{limit}} results
{{/limit}}
```

### Behaviour

- **Empty `options`** (default): tool returns raw JSON data, no template rendering
- **Non-empty `options`**: tool renders output via its display template with options merged into context
- To request formatted output with no special options, pass `options=["formatted"]`

### Command template usage

```mustache
{{tool_prefix}}list_exports(
    options=["formatted", "verbose"])
```

Or with key=value:

```mustache
{{tool_prefix}}list_exports(
    options=["formatted", "limit=10"])
```

## Consequences

- Tool signatures remain stable as new display options are added
- Templates control presentation without tool code changes
- Options are self-documenting in the template
- No validation of option names at the tool level — unknown options are silently ignored by templates
- Key=value pairs are always strings; templates or tools must handle type coercion if needed
- Convention: tools that support `options` should document recognised values in their docstring
