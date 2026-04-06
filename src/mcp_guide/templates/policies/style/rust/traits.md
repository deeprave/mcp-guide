---
type: agent/instruction
description: >
  Style Policy: Trait-Based Design (Rust). Use traits to define shared behaviour and enable polymorphism.
---
# Style Policy: Trait-Based Design (Rust)

Use traits to define shared behaviour and enable polymorphism.

## Rules

- Define traits for behaviour that multiple types should share
- Prefer static dispatch (generics with trait bounds) over dynamic dispatch (`dyn Trait`)
  unless object safety or heterogeneous collections are required
- Implement standard traits (`Display`, `Debug`, `From`, `Into`, `Iterator`) where appropriate
- Keep trait interfaces focused — one concern per trait

## Rationale

Traits are Rust's primary abstraction mechanism. Static dispatch gives zero-cost
abstractions; dynamic dispatch gives runtime flexibility when needed.
