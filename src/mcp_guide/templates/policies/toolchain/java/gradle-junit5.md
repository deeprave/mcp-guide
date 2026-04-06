---
type: agent/instruction
description: >
  Toolchain Policy: Gradle + JUnit 5 (Java)
---
# Toolchain Policy: Gradle + JUnit 5 (Java)

| Role | Tool |
|---|---|
| Build | `gradle` (Kotlin DSL preferred) |
| Test runner | `junit5` |
| Assertions | `assertj` |
| Mocking | `mockito` |
| Code style | `checkstyle` or `spotless` |

## Key commands

```bash
./gradlew test
./gradlew check
./gradlew spotlessApply
```

## Rationale

Gradle with Kotlin DSL offers better IDE support and type safety in build scripts
compared to Groovy DSL or Maven XML.
