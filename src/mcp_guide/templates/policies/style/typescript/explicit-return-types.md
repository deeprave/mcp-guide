---
type: agent/instruction
description: >
  Style Policy: Explicit Return Types (TypeScript). Always annotate the return type of exported functions and methods.
---
# Style Policy: Explicit Return Types (TypeScript)

Always annotate the return type of exported functions and methods.

## Rules

- All exported functions and public class methods must have explicit return types
- Internal/private functions may rely on inference where the type is obvious
- Async functions should annotate as `Promise<T>` not just `T`

## Rationale

Explicit return types serve as documentation and catch accidental type drift
when implementation changes.
