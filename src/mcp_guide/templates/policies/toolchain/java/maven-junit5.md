---
type: agent/instruction
description: >
  Toolchain Policy: Maven + JUnit 5 (Java)
---
# Toolchain Policy: Maven + JUnit 5 (Java)

| Role | Tool |
|---|---|
| Build | `maven` |
| Test runner | `junit5` (JUnit Jupiter) |
| Assertions | JUnit 5 assertions or `assertj` |
| Mocking | `mockito` |
| Code style | `checkstyle` |

## Key commands

```bash
mvn test
mvn verify
mvn checkstyle:check
```
