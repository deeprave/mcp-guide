# Design: Refactor FeatureValue

## Summary

The current `FeatureValue` is a type alias, not a real runtime abstraction. The
refactor introduces an opaque feature-value type with explicit conversion
boundaries.

## Goals

- create a real runtime type for feature flag values
- centralize validation, normalization, serialization, and display formatting
- reduce reliance on broad `Any` flows in flag-handling code
- preserve existing persisted/user-facing value syntax

## Non-Goals

- changing the supported user-facing flag shapes
- bundling unrelated workflow-render behavior changes into this refactor
- changing `IndexedList` or generic template list semantics

## Proposed Shape

Introduce a `FeatureValue` class or equivalent opaque abstraction that:

- stores a validated normalized underlying value
- exposes explicit conversion helpers such as:
  - `to_raw()`
  - `to_display()`
- optionally exposes typed inspection helpers where they meaningfully simplify
  flag consumers

The internal raw shape may still be scalar/list/dict-based, but callers should
stop treating feature values as arbitrary nested Python data by default.

## Integration Points

The refactor will likely need coordinated changes in:

- feature flag validators and normalizers
- project/global flag storage interfaces
- config/project models
- flag resolution helpers
- rendering cache and display-oriented projections
- tool responses that expose flag values

## Migration Strategy

Preferred migration path:

1. Introduce the opaque type with construction from currently valid raw values.
2. Update storage/model boundaries to wrap and unwrap values explicitly.
3. Update rendering and tool layers to consume the abstraction rather than raw
   nested values.
4. Keep config file serialization compatible with the current raw formats.

## Risks

- broad internal touch surface across flags, models, tools, and rendering
- accidental leakage of wrapper objects into serialization or templating
- over-designing typed accessors before actual usage patterns justify them

## Validation

Tests should cover:

- construction from all currently supported raw flag shapes
- round-trip serialization back to raw values
- display formatting for booleans, lists, dicts, and nested combinations
- compatibility of project/global flag storage and resolution
- unchanged user-facing config syntax
