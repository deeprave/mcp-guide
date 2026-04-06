---
type: agent/instruction
description: >
  Style Policy: Smart Pointers (C++). Prefer smart pointers over raw owning pointers.
---
# Style Policy: Smart Pointers (C++)

Prefer smart pointers over raw owning pointers.

## Rules

- Use `std::unique_ptr` for single ownership
- Use `std::shared_ptr` only when shared ownership is genuinely required
- Use raw pointers only for non-owning references (observation)
- Do not call `delete` manually — ownership is managed by smart pointers
- Do not use `new` directly; use `std::make_unique` and `std::make_shared`

## Rationale

Smart pointers enforce RAII and eliminate a class of memory leaks and
use-after-free bugs.
