---
type: agent/instruction
description: >
  Style Policy: Error Handling (Go). Handle errors explicitly and immediately at the call site.
---
# Style Policy: Error Handling (Go)

Handle errors explicitly and immediately at the call site.

## Rules

- Always check returned errors; never assign to `_` unless the error is genuinely irrelevant
- Return errors up the call stack with context using `fmt.Errorf("...: %w", err)`
- Use `errors.Is` and `errors.As` for error inspection, not string matching
- Reserve `panic` for programmer errors (invariant violations), not runtime conditions
- Use sentinel errors (`var ErrFoo = errors.New(...)`) for errors callers need to check

## Rationale

Go's explicit error handling makes failure paths visible and forces the caller to
decide how to handle them.
