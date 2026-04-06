---
type: agent/instruction
description: >
  Tooling Policy: No tr. Do not use `tr` for character-level text transformation in automated tasks.
---
# Tooling Policy: No tr

Do not use `tr` for character-level text transformation in automated tasks.

## Forbidden

- `tr` for case conversion, character deletion, or squeezing in pipelines

## Use instead

- Language-native string methods (`.lower()`, `.upper()`, `.replace()`, etc.)

## Rationale

`tr` only handles single-byte characters and silently produces incorrect results
on multi-byte (UTF-8) input. Language string methods are encoding-aware.
