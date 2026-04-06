---
type: agent/instruction
description: >
  Style Policy: Optional Usage (Java). Use `Optional<T>` for method return types that may produce no value.
---
# Style Policy: Optional Usage (Java)

Use `Optional<T>` for method return types that may produce no value.

## Rules

- Return `Optional<T>` from methods that may have no result instead of returning `null`
- Do not use `Optional` as a field type or parameter type
- Do not call `.get()` without first checking `isPresent()` — prefer `orElse`, `orElseThrow`, `ifPresent`, `map`

## Rationale

`Optional` makes the possibility of absence explicit in the API and eliminates
a class of NullPointerExceptions.
