---
type: agent/instruction
description: >
  Style Policy: Goroutines and Channels (Go). Use goroutines and channels deliberately with clear ownership.
---
# Style Policy: Goroutines and Channels (Go)

Use goroutines and channels deliberately with clear ownership.

## Rules

- Every goroutine must have a defined owner responsible for ensuring it terminates
- Use `context.Context` for cancellation propagation
- Do not use goroutines for parallelism without measuring the need
- Prefer channels for communication between goroutines; prefer mutexes for shared state protection
- Document goroutine lifetime in comments when it is not obvious

## Rationale

Goroutine leaks are a common source of bugs. Explicit ownership and cancellation
prevent goroutines from running indefinitely.
