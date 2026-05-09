## Why

Feature flag handling is currently too permissive and too inconsistent. Boolean
flags can leak through as strings like `"true"` or `"false"`, and some flag
usage still relies on hand-coded names instead of shared constants, which makes
flag resolution and requirement checking less reliable than it should be.

## What Changes

- Tighten the default feature flag model so flags are treated as either boolean
  (`true`/`false`) or arbitrary strings unless a flag explicitly registers a
  different validator and normaliser
- Introduce a default boolean-or-string validator and normaliser that applies to
  unregistered flags and any registered flag that does not override the default
  behavior
- Ensure boolean-looking inputs normalize to actual booleans rather than string
  values when persisted and resolved
- Audit existing built-in flags and route them through `FLAG_` constants instead
  of repeated hand-coded string literals wherever constants are missing or not
  yet used
- Preserve existing specialised flag behaviors for list-, dict-, or path-based
  flags that already define custom validation and normalization

## Capabilities

### New Capabilities
- `feature-flag-normalization`: Generic default validation and normalization for
  boolean-or-string feature flags, including canonical boolean coercion for
  `true` and `false`

### Modified Capabilities
- `config-manager`: Tighten project and global feature-flag storage and mutation
  so default flag typing and normalization are applied consistently
- `models`: Update the feature flag value model and related configuration
  assumptions to reflect the default boolean-or-string behavior for generic
  flags
- `workflow-flags`: Ensure workflow-related boolean flags rely on actual boolean
  values and remain compatible with the tightened default normalization rules

## Impact

- Affected code in `src/mcp_guide/feature_flags/`, workflow flag resolution, and
  feature-flag tools
- Potential updates to built-in flag constants and call sites that still use
  raw flag name strings
- Additional tests for flag normalization, validation, persistence, and
  requirement checking across both built-in and user-defined flags
