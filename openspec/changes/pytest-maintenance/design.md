## Context

The repository uses pytest and anyio across 181 test modules. The suite contains
unit, integration, protocol, and behavioural coverage, but its size has made
complete verification expensive. See [proposal.md](proposal.md) for the
motivation and maintenance scope.

## Goals / Non-Goals

**Goals:**

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
- Combining tests that differ in setup, observable behaviour, or diagnostic
  value.
- Removing compatibility coverage for a supported protocol or user-facing
  contract merely because its test name contains "legacy" or "migration".

## Decisions

- Audit by production area, not by test-name pattern alone. Names such as
  `legacy`, `migration`, or `exists` are triage signals; removal requires
  confirming that the test is not protecting a supported behaviour.
- Prefer removal when another test proves the same observable result with equal
  or broader setup. Prefer parametrisation only when setup and assertions are
  structurally identical; otherwise retain independently named scenarios.
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
- [Audit changes could accidentally weaken compatibility] → Explicitly record
  whether each migration or legacy test protects a currently supported contract
  before removing it.
