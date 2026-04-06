---
type: agent/instruction
description: >
  Style Policy: Strict Mode (TypeScript). Enable TypeScript strict mode in `tsconfig.json`.
---
# Style Policy: Strict Mode (TypeScript)

Enable TypeScript strict mode in `tsconfig.json`.

## Rules

- `"strict": true` in `tsconfig.json` (enables all strict checks)
- Do not disable individual strict flags without documented justification
- Treat type errors as build failures

## Rationale

Strict mode catches a wide class of bugs at compile time. The short-term cost
of fixing strict errors pays off quickly in reduced runtime surprises.
