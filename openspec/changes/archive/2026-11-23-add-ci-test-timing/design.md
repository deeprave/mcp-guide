# Design

## Context

The test workflow runs the full suite for Python 3.13, 3.14, and 3.15. It currently writes and uploads JUnit duration data only for 3.14, leaving an unusually slow result in another matrix entry without comparable per-test evidence. A single CI run cannot establish an interpreter-performance regression: hosted-runner variation, dependency differences, and test-level timing all remain possible causes. The retained reports enable those hypotheses to be examined across repeated runs.

## Goals / Non-Goals

**Goals:**

- Produce one duration report per test-matrix version.
- Name artifacts so their Python version is evident without opening them.
- Keep all version jobs running the same complete test selection.
- Analyse repeated comparable reports to identify whether particular tests explain the Python 3.13 difference, or whether the difference is broadly distributed.

**Non-Goals:**

- Change which tests run in CI.
- Gate CI or alter its pass/fail outcome based on timing data.
- Optimise individual test durations in this change.

## Decisions

### Emit JUnit durations for every matrix job

Each job will pass the same JUnit output and duration-report options to pytest. This makes the reports directly comparable and avoids special-case test invocation paths. The existing 3.14-only condition is removed.

### Upload a versioned timing artifact from every job

The upload step will run for every matrix entry and include the matrix Python version in its artifact name. Artifact data remains diagnostic only; test success remains the CI gate.

### Analyse timing evidence after comparable runs

After reports have been collected from repeated comparable CI runs, compare their overall and per-test call durations across Python versions. The analysis will identify materially affected tests where present and distinguish a concentrated difference from a broad slowdown or runner variation; it will not make performance claims from a single run.

## Risks / Trade-offs

- [Additional artifact storage] → JUnit timing XML is small and is limited to one file per supported Python version.
- [Timing varies by hosted runner] → Comparing reports identifies persistent test-level differences while retaining the runner context as a source of variance.
