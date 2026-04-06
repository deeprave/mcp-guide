---
type: agent/instruction
description: >
  Methodology Policy: Test-Driven Development (TDD). The agent follows the Red-Green-Refactor cycle for all new functionality.
---
# Methodology Policy: Test-Driven Development (TDD)

The agent follows the Red-Green-Refactor cycle for all new functionality.

## Rules

- Write a failing test before writing any production code
- Write only enough test code to demonstrate a failure
- Write only enough production code to make the failing test pass
- Refactor immediately after green; do not accumulate technical debt
- Each cycle should take minutes, not hours
- Commit after each successful cycle
- Let tests drive the design

## Common mistakes to avoid

- Writing tests after the implementation
- Making increments too large
- Skipping the refactor phase
- Testing implementation details instead of behaviour

## Rationale

TDD produces well-tested code and lets the test suite serve as executable
specification. Best suited to teams comfortable with the discipline of
writing tests first.
