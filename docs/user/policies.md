# Policy Selection

Policies let you tell your AI agent how you prefer to work — which methodology to follow, how strict to be with tests, what git operations are allowed, and more.

## What are Policies?

Your AI agent makes a lot of small decisions while working: how to write commit messages, whether to write tests first, how cautious to be with git operations, which style conventions to follow. Policies are where you tell it your preferences.

Each **topic** has a set of policy documents to choose from. Selecting a policy for a topic activates those preferences across all relevant templates — guides, checks, reviews, and context documents.

If no policy is selected for a topic, the agent will note that no preference has been set and proceed without enforcing anything specific for it.

## Topics

Policies are organised into topics. Here are the available topics and what they control:

| Topic | What it controls |
|-------|-----------------|
| `methodology` | Development approach: TDD, BDD, SOLID, YAGNI, DDD |
| `testing` | How strictly the agent follows test structure rules |
| `quality` | How warnings and coverage thresholds are enforced |
| `review` | How thorough code reviews are |
| `git/ops` | Which git operations the agent may perform |
| `git/commit` | Commit message format |
| `pr` | Pull request description format |
| `style/<language>` | Language-specific style preferences |
| `toolchain/<language>` | Which build tools, test runners, and formatters to use |
| `tooling/general` | Specific tools the agent should avoid |

## Selecting Policies

Just ask your AI agent to make the selection for you:

```
Use TDD methodology for this project
Set git operations to conservative — read-only
Use conventional commits
Use the uv + ruff + pytest toolchain for Python
```

The agent will update your project's policy configuration directly.

You can also ask what's available for a topic:

```
What methodology policies are available?
What are my options for git commit format?
```

## Mutually Exclusive Topics

Some topics are **mutually exclusive** — selecting one replaces any previous selection. It doesn't make sense to enforce both strict and minimal testing at the same time, for example, so only one option per topic is active at once.

Mutually exclusive topics include:

- `testing` — pick one: strict, pragmatic, or minimal
- `quality` — pick one: zero-tolerance, standard, or relaxed
- `review` — pick one: thorough, focused, or minimal
- `git/ops` — pick one: no-git-ops, conservative, agent-assisted, or agent-autonomous
- `git/commit` — pick one: imperative, conventional, or minimal
- `pr` — pick one: github-standard, minimal, or no-prs
- `style/<language>` — each language slot is independent, but pick one per language
- `toolchain/<language>` — each language slot is independent, but pick one per language

## Combining Policies

Other topics are designed to be **combined**. Methodology is the clearest example — you can layer multiple complementary principles:

```
Use TDD, SOLID, and YAGNI for this project
```

This activates all three together. Each policy document is injected in sequence, so the agent receives all of them when working.

Tooling prohibitions (`tooling/general`) work the same way — you can select as many as apply to your project:

```
Prohibit sed, awk, and perl for this project
```

## Available Policies

### Methodology (`methodology/`)

| Policy | Description |
|--------|-------------|
| `tdd` | Test-Driven Development — write failing tests before production code |
| `bdd` | Behaviour-Driven Development — frame the work in terms of observable behaviours |
| `solid` | SOLID principles — single responsibility, open/closed, Liskov, interface segregation, dependency inversion |
| `yagni` | YAGNI — don't build things until there's a concrete, immediate need |
| `ddd` | Domain-Driven Design — structure code around the core domain model |

### Testing (`testing/`)

| Policy | Description |
|--------|-------------|
| `strict` | Strong structural rules apply — no conditionals in tests, no raw loops, no mocks |
| `pragmatic` | Structural rules are guidance — mocks are permitted when useful (default) |
| `minimal` | Test that things work — no structural rules beyond basic correctness |

### Quality (`quality/`)

| Policy | Description |
|--------|-------------|
| `zero-tolerance` | All warnings are errors, coverage thresholds enforced |
| `standard` | Warnings are addressed; coverage expectations are reasonable but not absolute (default) |
| `relaxed` | Focus on correctness — coverage not enforced, warnings are informational |

### Review (`review/`)

| Policy | Description |
|--------|-------------|
| `thorough` | Full review covering correctness, security, and all active methodology principles |
| `focused` | Review correctness and security only — skip methodology and style (default) |
| `minimal` | Quick sanity check for obvious bugs and security issues only |

### Git Operations (`git/ops/`)

| Policy | Description |
|--------|-------------|
| `no-git-ops` | Agent must never perform git operations autonomously |
| `conservative` | Agent may use read-only git operations — no writes unless explicitly requested (default) |
| `agent-assisted` | Agent may stage and commit with explicit per-request consent — no push without instruction |
| `agent-autonomous` | Agent may perform all git operations including push without per-operation consent |

### Commit Format (`git/commit/`)

| Policy | Description |
|--------|-------------|
| `imperative` | Imperative mood with structured body |
| `conventional` | Conventional Commits format — enables automated changelogs and semantic versioning (default) |
| `minimal` | Subject line only — no format rules beyond that |

### Pull Requests (`pr/`)

| Policy | Description |
|--------|-------------|
| `github-standard` | Structured four-section format: overview, changes, impact, notes |
| `minimal` | Title and brief summary only |
| `no-prs` | This team doesn't use pull requests — commit directly |

### Style

Each language has its own style slot. Ask your agent what's available for your language:

```
What Python style policies are available?
What TypeScript style options do you have?
```

### Toolchain

Each language has its own toolchain slot:

```
What Python toolchain policies are available?
```

Common examples: `uv + ruff + pytest` for Python, `pnpm + biome + vitest` for TypeScript.

### Tooling Prohibitions (`tooling/general/`)

These can be combined freely:

| Policy | Description |
|--------|-------------|
| `no-sed` | Don't use `sed` for file content transformation |
| `no-awk` | Don't use `awk` for file or stream processing |
| `no-perl` | Don't use `perl` one-liners as a shell text-processing tool |
| `no-tr` | Don't use `tr` for character-level text transformation |

## Reviewing Your Current Policies

Ask your agent to show you what's currently active:

```
What policies are configured for this project?
Show me my current policy selections
```

## Changing a Policy

Just ask:

```
Switch from TDD to BDD
Change git operations to agent-assisted
Use the standard quality policy instead of zero-tolerance
```

The agent will update the selection for that topic and the old policy is replaced.
