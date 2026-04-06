---
type: agent/instruction
description: >
  Toolchain Policy: CMake + GoogleTest (C++)
---
# Toolchain Policy: CMake + GoogleTest (C++)

| Role | Tool |
|---|---|
| Build | `cmake` + `ninja` or `make` |
| Test runner | `googletest` (gtest + gmock) |
| Formatter | `clang-format` |
| Static analysis | `clang-tidy` |

## Key commands

```bash
cmake -B build -G Ninja
cmake --build build
ctest --test-dir build
clang-format -i src/**/*.cpp src/**/*.h
```
