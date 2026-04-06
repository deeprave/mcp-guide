---
type: agent/instruction
description: >
  Style Policy: Null Safety (Kotlin). Treat the `!!` (not-null assertion) operator as a code smell.
---
# Style Policy: Null Safety (Kotlin)

Treat the `!!` (not-null assertion) operator as a code smell.

## Rules

- Do not use `!!` except in tests or where nullability is guaranteed by an external contract
- Use `?.`, `?:`, `let`, `also`, `run` for safe null handling
- Use `requireNotNull()` or `checkNotNull()` with a message when asserting non-null is correct
- Prefer non-nullable types in APIs; push nullability to the edges

## Rationale

`!!` converts a compile-time safety guarantee into a runtime exception.
Handling nulls explicitly is the point of Kotlin's type system.
