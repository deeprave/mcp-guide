---
type: agent/instruction
description: >
  Toolchain Policy: pnpm + biome + vitest (TypeScript)
---
# Toolchain Policy: pnpm + biome + vitest (TypeScript)

| Role | Tool |
|---|---|
| Package manager | `pnpm` |
| Compiler | `tsc` |
| Formatter + linter | `biome` |
| Test runner | `vitest` |

## Key commands

```bash
pnpm add -D typescript @biomejs/biome vitest
pnpm exec tsc --noEmit
pnpm exec biome check --write .
pnpm test
```

## Rationale

`biome` handles both formatting and linting without the eslint + prettier
configuration overhead. `vitest` has native TypeScript support.
