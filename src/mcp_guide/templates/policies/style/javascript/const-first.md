---
type: agent/instruction
description: >
  Style Policy: Const-First (JavaScript). Use `const` by default; use `let` only when reassignment is required. Never use `var`.
---
# Style Policy: Const-First (JavaScript)

Use `const` by default; use `let` only when reassignment is required. Never use `var`.

## Rules

- Declare all variables with `const` unless they will be reassigned
- Use `let` only when a variable's value changes after initial assignment
- Never use `var`

## Rationale

`const` makes intent explicit and prevents accidental reassignment.
`var` has function scope and hoisting behaviour that leads to bugs.
