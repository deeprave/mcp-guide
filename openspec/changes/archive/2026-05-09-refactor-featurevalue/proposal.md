# Refactor FeatureValue

## Why

Feature flags are currently represented as a broad runtime union of plain Python
values:

- `bool`
- `str`
- `list[str]`
- `dict[str, str | list[str]]`

This is convenient but too permissive as an architectural boundary. Flag values
flow through validation, normalization, resolution, rendering, storage, and
tool output as loosely-typed nested structures. That makes it easy to rely on
`Any`-shaped behavior in intermediate code and makes it harder to centralize:

- validation and invariants
- normalization
- display formatting
- serialization
- type-safe access patterns

The workflow-render issue exposed one symptom of this: display-oriented code had
to reason about the raw runtime shape of flags instead of a dedicated feature
value abstraction.

## What Changes

1. Replace the current plain `FeatureValue` type alias with a real runtime
   feature-value abstraction.
2. Ensure flag values are validated and normalized through that abstraction
   rather than being passed around as loosely-typed nested data.
3. Provide dedicated helpers on the abstraction for:
   - raw serialization
   - display formatting
   - safe typed access where needed
4. Update flag validation, resolution, storage, and rendering paths to use the
   new abstraction consistently.
5. Preserve the current externally supported flag value shapes for users and
   configuration files.

## Impact

- Affected specs:
  - `workflow-flags`
  - `template-rendering`
  - `tool-infrastructure`
  - `project-config`
- Affected code:
  - `src/mcp_guide/feature_flags/`
  - config and project models
  - session/config persistence
  - rendering and template-context assembly
  - feature-flag tools and flag resolution helpers
- Breaking changes:
  - internal API refactor only; persisted/user-facing flag syntax should remain
    compatible
