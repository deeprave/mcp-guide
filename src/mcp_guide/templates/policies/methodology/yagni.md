---
type: agent/instruction
description: >
  Methodology Policy: YAGNI. Do not implement something until there is a concrete, immediate need for it.
---
# Methodology Policy: YAGNI

Do not implement something until there is a concrete, immediate need for it.

## Rules

- Implement features when required, not in anticipation
- Do not build infrastructure for hypothetical use cases
- Do not generalise from a single use case
- Do not add configuration for future flexibility
- Do not optimise before measuring
- Wait for a third occurrence before abstracting

## Red flags

These phrases indicate a likely YAGNI violation:
- "We might need this later"
- "This will make it more flexible"
- "Let's make it configurable"
- "What if we need to..."

## Rationale

Speculative features cost development time, increase complexity, and are often
wrong. YAGNI keeps codebases smaller and easier to change.
