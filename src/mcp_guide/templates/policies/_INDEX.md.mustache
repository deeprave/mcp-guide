# Policies Index

This directory contains optional policy documents expressing development preferences.
Policies are plain markdown files organised by topic and sub-topic.

Select policies by adding patterns to the `policies` category in project configuration:

```yaml
categories:
  policies:
    patterns:
      - git/ops/no-git-ops
      - git/commit/conventional
      - testing/pragmatic
      - methodology/yagni
      - methodology/solid
      - quality/standard
      - style/python/async-first
      - style/python/comprehensions
      - toolchain/python/uv-ruff-pytest
      - review/focused
```

Files prefixed with `_` (like this one) are excluded from pattern matching and content delivery.

**Note:** Workflow phase configuration is controlled by the `workflow` and `workflow-consent`
project flags, not by policies.

---

## Topics

### `git/ops/` — Git Operation Delegation
**Mutually exclusive.**

| File | Summary |
|---|---|
| `no-git-ops` | Agent never touches git (default) |
| `conservative` | Read-only ops permitted; no staging or commits |
| `agent-assisted` | Agent may stage and commit with explicit per-request consent |
| `agent-autonomous` | Agent manages git fully including push |

*Affects: `guide/general.mustache`*

---

### `git/commit/` — Commit Message Format
**Mutually exclusive.**

| File | Summary |
|---|---|
| `imperative` | Imperative mode, 72-char subject, structured body (default) |
| `conventional` | Conventional Commits: `feat:`, `fix:`, `chore:`, etc. |
| `minimal` | Subject line only; no format rules |

*Affects: `review/commit.mustache`*

---

### `testing/` — Testing Strictness
**Mutually exclusive.**

| File | Summary |
|---|---|
| `strict` | No mocks, no conditionals, no loops in tests (default) |
| `pragmatic` | Mocks when needed; structure is guidance not mandate |
| `minimal` | Test that things work; no structural rules |

*Affects: `checks/testing.mustache`*

---

### `methodology/` — Development Methodologies
**Composable — select one or more.**

| File | Summary |
|---|---|
| `tdd` | Test-Driven Development — tests written before implementation |
| `bdd` | Behaviour-Driven Development |
| `yagni` | YAGNI — never implement features speculatively |
| `solid` | SOLID object-oriented design principles |
| `ddd` | Domain-Driven Design |

*Affects: `guide/tdd.mustache`, `guide/yagni.mustache`, `guide/solid.mustache`,
`guide/bdd.mustache`, `guide/ddd.mustache`, `review/general.mustache`*

---

### `quality/` — Code Quality Tolerance
**Mutually exclusive.**

| File | Summary |
|---|---|
| `zero-tolerance` | All warnings are errors; coverage threshold enforced (default) |
| `standard` | Warnings addressed; reasonable coverage expectations |
| `relaxed` | Focus on correctness; coverage not enforced |

*Affects: `checks/python.mustache`, `lang/python.mustache`*

---

### `style/<language>/` — Language Style Preferences
**Composable within a language — select any applicable.**
**Mutually exclusive across languages** (select one language's style set).

#### `style/python/`
`async-first`, `comprehensions`, `walrus`, `enum-over-chains`

#### `style/javascript/`
`async-await`, `arrow-functions`, `esm`, `const-first`

#### `style/typescript/`
`strict-mode`, `no-any`, `type-aliases`, `explicit-return-types`

#### `style/java/`
`streams`, `optional`, `modern-java`

#### `style/kotlin/`
`coroutines`, `null-safety`, `data-classes`

#### `style/cpp/`
`modern-cpp`, `smart-pointers`, `raii`

#### `style/golang/`
`error-handling`, `interfaces`, `goroutines`

#### `style/rust/`
`error-handling`, `ownership`, `traits`

---

### `toolchain/<language>/` — Toolchain Choices
**Mutually exclusive within a language.**

#### `toolchain/python/`
`uv-ruff-pytest` (default/modern), `poetry-black-pytest`, `pip-pytest`

#### `toolchain/javascript/`
`npm-eslint-jest`, `pnpm-eslint-vitest`, `bun-biome-vitest`

#### `toolchain/typescript/`
`npm-eslint-jest`, `pnpm-biome-vitest`

#### `toolchain/java/`
`gradle-junit5` (recommended), `maven-junit5`

#### `toolchain/kotlin/`
`gradle-kotest` (recommended), `gradle-junit5`

#### `toolchain/cpp/`
`cmake-gtest`, `cmake-catch2`

#### `toolchain/golang/`
`standard-testify` (recommended), `standard-only`

#### `toolchain/rust/`
`cargo-nextest` (recommended), `cargo-standard`

---

### `pr/` — Pull Request Format
**Mutually exclusive.**

| File | Summary |
|---|---|
| `github-standard` | PR with Overview / Changes / Impact / Notes (default) |
| `minimal` | Title and brief summary only |
| `no-prs` | Team uses direct commits or squash |

*Affects: `review/pr.mustache`*

---

### `review/` — Review Thoroughness
**Mutually exclusive.**

| File | Summary |
|---|---|
| `thorough` | Full review: security, correctness, methodology compliance (default) |
| `focused` | Correctness and security only |
| `minimal` | Quick sanity check |

*Affects: `review/general.mustache`*

---

### `tooling/general/` — Cross-Language Tool Restrictions
**Composable — select any combination.**

| File | Summary |
|---|---|
| `no-sed` | Do not use `sed` for file content transformation |
| `no-awk` | Do not use `awk` for text processing in automated tasks |
| `no-perl` | Do not use `perl` one-liners for inline text transformation |
| `no-tr` | Do not use `tr`; use language-native string methods instead |

---

## Mutual Exclusivity Notes

Within each of these topics, only one file should be active at a time:
`git/ops`, `git/commit`, `testing`, `quality`, `toolchain/<language>`, `pr`, `review`

These topics are fully composable (select any combination):
`methodology`, `style/<language>`, `tooling/general`
