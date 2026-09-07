## Context

The repository uses pytest and anyio across 181 test modules. The suite contains
unit, integration, protocol, and behavioural coverage, but its size has made
complete verification expensive. See [proposal.md](proposal.md) for the
motivation and maintenance scope.

## Goals / Non-Goals

**Goals:**

- Reduce full-suite wall-clock runtime; test count and source size are supporting
  measurements, not substitutes for runtime improvement.
- Establish a production-behaviour map for every test module before changing
  it, so removal decisions are evidence based.
- Retain one clear regression path for every supported public contract and
  meaningful failure mode.
- Remove duplication and implementation-coupled coverage, and combine truly
  equivalent cases with pytest parametrisation.
- Measure the resulting collection count and full-suite duration.

**Non-Goals:**

- Changing Guide behaviour, public APIs, or test infrastructure solely to make
  tests shorter.
- Combining unrelated behaviours into monolithic tests or introducing shared
  mutable state between tests.
- Removing legacy or compatibility MCP protocol coverage.

## Decisions

- Audit by production area, not by test-name pattern alone. Names such as
  `legacy`, `migration`, or `exists` are triage signals; removal requires
  identifying what it actually covers. Remove application-compatibility and
  legacy-state tests, but retain MCP protocol compatibility tests. Preserve any
  current behaviour also exercised by a removed test in retained behavioural
  coverage.
- Remove tests targeting removed features, tools, classes or functions; do not
  recreate removed production surfaces to keep their tests passing.
- Replace temporary TDD-only and implementation-focused checks with combined
  behavioural tests. Extend a comprehensive scenario with related observable
  outcomes instead of repeating its setup in several single-behaviour tests.
- Prefer removal when another test proves the same observable result with equal
  or broader setup. Prefer parametrisation only when setup and assertions are
  structurally identical; otherwise retain independently named scenarios.
- Parametrisation alone still executes each parameter case and is not evidence
  of a speed improvement. Remove duplicate cases and repeated expensive work;
  compare baseline and final full-suite durations under equivalent conditions.
- Treat mocks at system boundaries as valid when no lightweight substitute is
  available. Replace internal mock-call assertions with observable state,
  returned payloads, persisted data, or emitted instructions when practical.
- Apply changes in production-area batches. Each batch runs its focused tests;
  the final batch runs the complete suite in a foreground PTY, preserving the
  repository's verification requirement.

## Risks / Trade-offs

- [A concise test may cover a unique edge case] → Cross-reference production
  branches and existing tests before removal; retain a behaviour-focused test
  where it is the sole regression guard.
- [Large parametrised matrices can hide failures] → Use meaningful case IDs and
  keep unrelated setup or assertions in separate tests.
- [Mock reduction can widen scope] → Replace mocks only when a lightweight,
  deterministic substitute exists; otherwise preserve the boundary mock.
- [Audit changes could accidentally weaken protocol compatibility] → Explicitly
  distinguish application compatibility and legacy state from MCP protocol
  compatibility before removing tests.
