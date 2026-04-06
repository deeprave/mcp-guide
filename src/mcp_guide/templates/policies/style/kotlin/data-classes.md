---
type: agent/instruction
description: >
  Style Policy: Data Classes (Kotlin). Use data classes for value types and simple data carriers.
---
# Style Policy: Data Classes (Kotlin)

Use data classes for value types and simple data carriers.

## Rules

- Use `data class` for types whose primary purpose is holding data
- Prefer immutable properties (`val`) in data classes
- Use sealed classes/interfaces for closed hierarchies of types
- Use value classes (`@JvmInline value class`) for single-field wrappers where performance matters

## Rationale

Data classes provide `equals`, `hashCode`, `toString`, and `copy` automatically,
reducing boilerplate for value types.
