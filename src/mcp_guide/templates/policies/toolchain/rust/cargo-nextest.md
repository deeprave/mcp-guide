---
type: agent/instruction
description: >
  Toolchain Policy: Cargo + nextest (Rust)
---
# Toolchain Policy: Cargo + nextest (Rust)

| Role | Tool |
|---|---|
| Build + package manager | `cargo` |
| Test runner | `cargo-nextest` |
| Formatter | `rustfmt` |
| Linter | `clippy` |

## Key commands

```bash
cargo nextest run
cargo clippy -- -D warnings
cargo fmt --check
```

## Rationale

`nextest` provides faster test execution through parallel test isolation, better
output formatting, and improved flaky test detection compared to the built-in
`cargo test`.
