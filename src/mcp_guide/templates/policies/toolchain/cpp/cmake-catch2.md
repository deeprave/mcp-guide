---
type: agent/instruction
description: >
  Toolchain Policy: CMake + Catch2 (C++)
---
# Toolchain Policy: CMake + Catch2 (C++)

| Role | Tool |
|---|---|
| Build | `cmake` |
| Test runner | `catch2` |
| Formatter | `clang-format` |
| Static analysis | `clang-tidy` |

## Rationale

Catch2 is header-friendly and provides BDD-style `SCENARIO`/`GIVEN`/`WHEN`/`THEN`
macros as well as standard `TEST_CASE`. Lighter setup than GoogleTest for smaller projects.
