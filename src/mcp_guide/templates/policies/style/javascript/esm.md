---
type: agent/instruction
description: >
  Style Policy: ES Modules (JavaScript). Use ES module syntax (`import`/`export`) over CommonJS (`require`/`module.exports`).
---
# Style Policy: ES Modules (JavaScript)

Use ES module syntax (`import`/`export`) over CommonJS (`require`/`module.exports`).

## Rules

- Always use `import`/`export`
- Do not use `require()` except in tooling config files that mandate it
- Use named exports by default; default exports only when the module has a single clear primary export

## Rationale

ES modules are the standard. Named exports improve refactoring and tree-shaking.
