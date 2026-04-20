## Context

Feature flags currently support multiple raw value shapes, but the default
behavior for unregistered or loosely handled flags is not strict enough. In
practice, this allows boolean-looking values to survive as strings, which can
break downstream checks that expect actual booleans while still rendering as
`true` or `false` in user-facing output.

The feature flag system already has a registration model for validators and
normalisers. That makes this change a good fit for tightening the default path
instead of adding more ad hoc corrections in downstream consumers such as
workflow requirement matching.

This is cross-cutting because it affects:

- global and project feature flag mutation
- built-in flag registration
- typed feature value storage
- any code path that depends on normalized raw values

## Goals / Non-Goals

**Goals:**
- Make the default feature flag contract boolean-or-string unless a flag
  explicitly registers a different shape
- Normalize boolean-looking inputs to actual booleans before persistence and
  later resolution
- Preserve existing custom behavior for flags that intentionally use lists,
  dicts, or specialised string validation
- Audit built-in flags so code paths use shared `FLAG_` constants instead of
  hand-coded string literals where constants should exist
- Keep downstream consumers simple by ensuring they receive correctly typed flag
  values from the feature flag layer

**Non-Goals:**
- Removing support for existing specialised flag types such as workflow phase
  lists, path flags, or consent mappings
- Redesigning the entire feature flag API surface or storage model
- Introducing a richer typed schema system for arbitrary user-defined flags
  beyond the default boolean-or-string contract

## Decisions

### Use a default validator and normaliser for generic flags

Unregistered flags, and registered flags that do not provide custom behavior,
should go through a shared boolean-or-string validator and normaliser.

This keeps the default rule explicit:

- `true` / `false` values are booleans
- any other accepted value is an arbitrary string

This is preferable to leaving generic flags fully unconstrained because the
current loose behavior is what allows stringly typed booleans to leak into the
runtime.

Alternative considered:
- Add downstream fixes in requirement checking and workflow logic. Rejected
  because it treats the symptoms while leaving the underlying flag typing bug in
  place.

### Preserve registered overrides as authoritative

Flags that already register a custom validator and normaliser must keep their
existing behavior. The default boolean-or-string behavior should only apply when
no more specific registration exists.

This preserves support for:

- workflow phase lists
- workflow consent mappings
- path flags
- any other built-in or future flags that need non-scalar values

Alternative considered:
- Force every flag through the same scalar-only rule. Rejected because it would
  break established built-in flags that intentionally use structured values.

### Normalize before storing wrapped FeatureValue objects

The feature flag mutation path should apply normalization before a value is
wrapped and stored. That ensures both persistence and later resolution use the
same canonical typed value, rather than relying on consumer-side conversions.

This also keeps display formatting honest: if a value renders as `true`, it
should really be the boolean `True`.

Alternative considered:
- Normalize only on read. Rejected because it leaves inconsistent values in
  stored project/global config and makes behavior dependent on which code path
  reads the flag.

### Audit built-in flags to prefer shared constants

Built-in flags should consistently use `FLAG_` constants at call sites so
behavior stays aligned across registration, mutation, resolution, and downstream
consumers.

This is not just style cleanup. It reduces drift where a built-in flag has a
registered validator but a call site still references a raw string that is easy
to mistype or duplicate.

Alternative considered:
- Limit the change to normalization only. Rejected because this work is already
  touching the built-in flag surface, and constant drift is a related source of
  inconsistency.

## Risks / Trade-offs

- [Generic user-defined flags currently rely on list or dict values] → Document
  that structured values require explicit flag registration and preserve
  existing built-in overrides
- [Input normalization changes persisted values for existing projects] → Limit
  coercion to boolean-looking values and retain arbitrary strings unchanged
- [Constant audit misses scattered raw literals] → Use repository-wide searches
  for built-in flag names and update obvious built-in call sites during the
  change
- [Default normalization order conflicts with existing custom normalisers] →
  Keep override precedence explicit so registered normalisers run instead of the
  default

## Migration Plan

1. Add shared default boolean-or-string validator and normaliser utilities
2. Update feature flag mutation paths to use default normalization unless a flag
   registration overrides it
3. Audit built-in flags and replace remaining raw literals with `FLAG_`
   constants where appropriate
4. Add regression coverage for:
   - boolean coercion
   - arbitrary string preservation
   - built-in flags with custom structured behavior
   - downstream requirement checks that depend on typed booleans

No manual migration should be required. Existing persisted string values that
spell boolean values may be normalized the next time they are updated through
the supported tooling.

Rollback is straightforward: restore the previous default validation behavior
and remove the generic normalisation path.

## Open Questions

- Should the default boolean-or-string normaliser accept case-insensitive string
  inputs like `TRUE` / `False`, or only canonical lowercase boolean spellings?
- Do we want a dedicated inventory of built-in feature flags and their allowed
  shapes in the specs, or is the registration code the source of truth?
