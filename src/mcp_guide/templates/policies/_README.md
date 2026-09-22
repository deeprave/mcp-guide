---
cache: long
---

# Policy Reference

This README is a repository reference for people maintaining policy documents.
It is not policy content and is not delivered to users or agents. Policies are
plain Markdown files organised by topic and sub-topic.

Files prefixed with `_` are excluded from pattern matching and content delivery,
so they may be used for shared partials and authoring references.

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

*Used by: `guide/general.mustache`; Git commit, Git push, Git sync, and Git PR skills*

---

### `git/commit/` — Commit Message Format
**Mutually exclusive.**

| File | Summary |
|---|---|
| `imperative` | Imperative mode, 72-char subject, structured body (default) |
| `conventional` | Conventional Commits: `feat:`, `fix:`, `chore:`, etc. |
| `minimal` | Subject line only; no format rules |

*Used by: `review/commit.mustache`; Git commit skill*

---

### `git/delivery/` — Delivery Strategy
**Mutually exclusive.**

| File | Summary |
|---|---|
| `direct` | Commit to the agreed target branch without a pull request |
| `branch` | Use an issue-aware branch and the configured pull-request practice |
| `multi-branch` | Keep concurrent changes isolated for later integration |

*Used by: Git commit, Git push, and Git PR skills*

### `issue-tracking/` — Issue Tracker
**Mutually exclusive.**

| File | Summary |
|---|---|
| `none` | No issue tracker is selected |
| `jira`, `linear`, `redmine`, `asana`, `youtrack` | Use the selected hosted issue tracker |
| `github-issues`, `gitlab`, `bugzilla`, `mantis`, `monday-com` | Use the selected issue platform |
| `trello`, `wrike`, `shortcut`, `trac`, `basecamp`, `phabricator` | Use the selected project or issue tracker |

A selected tracker makes issue handling available; the user still chooses
whether a particular change creates, links, or omits an issue.

*Used by: Git commit skill*

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

*Affects: `guide/methodology.mustache`, `review/general.mustache`*

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

## Authoring Policy-Aware Templates

Templates declare the policy topics they consume in frontmatter and render each
one as a Mustache partial. For example:

```yaml
policies: [git/delivery, issue-tracking]
```

```mustache
{{> git/delivery}}
{{> issue-tracking}}
```

Guide gathers only the project's selected documents for each declared topic
when it renders the template, including public Guide skill resources. Tests
should exercise rendered selected-versus-unselected behaviour using controlled
fixture documents rather than matching shipped policy prose.

---

## Mutual Exclusivity Notes

Within each of these topics, only one file should be active at a time:
`git/ops`, `git/commit`, `git/delivery`, `issue-tracking`, `testing`, `quality`, `toolchain/<language>`, `pr`, `review`

These topics are fully composable (select any combination):
`methodology`, `style/<language>`, `tooling/general`
