---
type: agent/instruction
description: >
  Style Policy: No Any (TypeScript). Avoid the `any` type. Use precise types, `unknown`, or generics instead.
---
# Style Policy: No Any (TypeScript)

Avoid the `any` type. Use precise types, `unknown`, or generics instead.

## Rules

- Do not use `any` in new code
- Replace existing `any` usages when touching surrounding code
- Use `unknown` when the type is genuinely unknown and narrow before use
- Use generics to express type relationships
- `@ts-ignore` and `@ts-expect-error` require a comment explaining why

## Rationale

`any` silently disables type checking. `unknown` forces explicit narrowing,
preserving safety.
