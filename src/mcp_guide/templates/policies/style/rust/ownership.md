---
type: agent/instruction
description: >
  Style Policy: Ownership and Borrowing (Rust). Work with the borrow checker, not against it.
---
# Style Policy: Ownership and Borrowing (Rust)

Work with the borrow checker, not against it.

## Rules

- Prefer borrowing (`&T`, `&mut T`) over cloning or moving unless ownership transfer is needed
- Use lifetimes explicitly only when the compiler cannot infer them
- Avoid `Rc<RefCell<T>>` unless shared mutable state is genuinely required — prefer message passing
- Do not use `unsafe` without a documented safety invariant and code review
- Prefer `Arc<Mutex<T>>` over `Rc<RefCell<T>>` in concurrent code

## Rationale

Fighting the borrow checker usually indicates a design problem. Working with
ownership patterns produces code that is correct by construction.
