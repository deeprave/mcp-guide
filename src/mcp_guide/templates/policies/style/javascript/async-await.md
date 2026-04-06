---
type: agent/instruction
description: >
  Style Policy: Async/Await (JavaScript). Prefer `async`/`await` over raw Promise chains or callbacks.
---
# Style Policy: Async/Await (JavaScript)

Prefer `async`/`await` over raw Promise chains or callbacks.

## Rules

- Use `async`/`await` for all asynchronous code
- Avoid `.then()`/`.catch()` chains except when composing independent promises with `Promise.all`
- Use `try`/`catch` for error handling in async functions
- Never mix callbacks and async/await in the same flow

## Rationale

`async`/`await` reads like synchronous code, making control flow and error handling clear.
