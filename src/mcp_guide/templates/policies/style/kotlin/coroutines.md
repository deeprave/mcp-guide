---
type: agent/instruction
description: >
  Style Policy: Coroutines (Kotlin). Prefer coroutines over callbacks or reactive streams for asynchronous code.
---
# Style Policy: Coroutines (Kotlin)

Prefer coroutines over callbacks or reactive streams for asynchronous code.

## Rules

- Use `suspend` functions for asynchronous operations
- Use structured concurrency with `coroutineScope`, `supervisorScope`
- Prefer `Flow` over callbacks for streams of values
- Use `Dispatchers.IO` for blocking I/O, `Dispatchers.Default` for CPU-bound work
- Do not use `GlobalScope`

## Rationale

Coroutines provide structured concurrency with readable, sequential-looking code
and explicit cancellation semantics.
