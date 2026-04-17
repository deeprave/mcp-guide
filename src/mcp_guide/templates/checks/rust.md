# Rust Testing Best Practices For Agents

## Purpose

Use the fastest checks that still protect correctness. Prefer small, repeatable commands and escalate to broader validation before finishing.

## Core Rules

- Test behaviour, not implementation details.
- Prefer public APIs in integration tests.
- Keep unit tests close to the code they exercise.
- Add or update tests with every behaviour change.
- Start with the smallest relevant check, then widen scope.
- Do not leave warnings unresolved; fix them.
- Avoid flaky tests, hidden global state, and time-sensitive assumptions.
- Keep test fixtures minimal and explicit.

## Standard Command Order

### 1. Typecheck early

```bash
cargo check
```

Use this first for quick feedback while editing.

### 2. Run targeted tests during development

```bash
cargo test <name>
```

Prefer targeted execution while iterating on a small change.

### 3. Run the full test suite with nextest

```bash
cargo nextest run
```

Prefer `cargo nextest` over `cargo test` for full-suite execution when available. It is faster, clearer, and better suited to repeated agent use.

### 4. Run lint checks strictly

```bash
cargo clippy --all-targets --all-features -- -D warnings
```

Treat warnings as failures. Do not suppress lints without explicit user approval.

### 5. Reconfirm basic compilation if needed

```bash
cargo check --all-targets --all-features
```

Use this when the change touches tests, examples, benches, or feature-gated code.

## Best Practices By Tool

## `cargo check`

- Use for fast structural feedback.
- Run before broader validation.
- Prefer `--all-targets --all-features` before closing out cross-cutting changes.

## `cargo nextest`

- Use for full validation and repeated test runs.
- Prefer targeted filters when debugging a failing test.
- Treat ignored or flaky tests as technical debt to call out explicitly.

## `cargo clippy`

- Run with `--all-targets --all-features`.
- Use `-D warnings` for final validation.
- Fix root causes instead of adding `allow` attributes unless explicitly justified.

## Test Design Guidance

- Unit tests: validate internal logic in small, deterministic cases.
- Integration tests: validate observable behaviour through public interfaces.
- Regression tests: add one for every bug fix that could reappear.
- Error-path tests: cover expected failures, not just happy paths.
- Concurrency tests: keep them deterministic and bounded.

## Completion Standard

Before declaring work complete, an agent should normally run:

```bash
cargo check --all-targets --all-features
cargo nextest run
cargo clippy --all-targets --all-features -- -D warnings
```

If any of these are skipped, say so explicitly and explain why.
