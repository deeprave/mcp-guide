---
type: agent/instruction
description: >
  Toolchain Policy: Gradle + Kotest (Kotlin)
---
# Toolchain Policy: Gradle + Kotest (Kotlin)

| Role | Tool |
|---|---|
| Build | `gradle` (Kotlin DSL) |
| Test runner | `kotest` |
| Mocking | `mockk` |
| Linter | `detekt` |

## Key commands

```bash
./gradlew test
./gradlew detekt
```

## Rationale

Kotest provides idiomatic Kotlin test DSLs with property-based testing built in.
`mockk` is purpose-built for Kotlin and handles coroutines, objects, and
extension functions naturally.
