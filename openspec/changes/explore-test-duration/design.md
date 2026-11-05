# Design

## Context

See proposal.md for motivation and `test-feedback-selection` for the behavioural
contract. The current local pytest pre-commit hook runs the complete suite with
coverage, while CI also runs complete pytest. `pytest-testmon` can select from
recorded runtime dependencies, but needs its own collected state; the existing
coverage configuration must not disable that collection. `pytest-impacted` offers
static, transitive import analysis but its documented Git modes do not directly
model the staged pre-commit index.

## Goals / Non-Goals

**Goals:**

- Reduce local commit feedback time without allowing incomplete local selection
  to relax full pull-request pytest execution.
- Trial a runtime dependency selector first, with a measured and reversible
  fallback path.
- Make test class and duration evidence available for subsequent decisions.

**Non-Goals:**

- Replacing the full pull-request suite, coverage policy, or required checks.
- Promising that every test will be narrowly selected on every change.
- Adding a permanent hosted timing database or changing production behaviour.

## Decisions

### Trial Testmon through a dedicated local hook

The pre-commit pytest hook will become a local affected-test trial that invokes
Testmon without receiving pre-commit filenames. Testmon's persistent state is
stored in an ignored project-local data file and seeded from a known complete
run. The hook disables the project's normal pytest-cov collection for this run
so Testmon can collect its own dependency data; complete CI continues to collect
coverage as it does today.

The trial treats untracked state, missing baseline data, failed selected tests,
and configured broad-impact files conservatively. It either refreshes the data
through the relevant suite or runs that suite, never silently reports an empty
selection as sufficient feedback.

Alternative considered: use `pytest-impacted` immediately. Rejected for the
first trial because its static Git modes need staged-index integration in the
pre-commit environment. It remains the fallback experiment if Testmon's runtime
selection is too broad, too narrow, or too operationally fragile.

### Preserve the full suite at the pull-request boundary

CI keeps the current complete pytest command as its authoritative check. The
local selector is advisory only in the sense that it accelerates feedback, not
in the sense that failures may be ignored. No PR or merge workflow is changed to
use selected tests instead of the full inventory.

Alternative considered: run integration tests only at commit time. Rejected:
integration tests have high value but are not reliably the highest coverage per
unit of feedback time, particularly for isolation and timing-sensitive paths.

### Classify tests from location, then add explicit exceptional marks

Register `unit`, `integration`, `synchronisation`, `timing`, and `slow` pytest
marks. A collection hook assigns unit or integration marks from the established
directory hierarchy. Tests that depend on timing or concurrent coordination add
their explicit marks at the test site, so those risks are visible even when a
test otherwise belongs to a broad location class.

Alternative considered: hand-mark every unit and integration test. Rejected
because it duplicates already meaningful directory structure and creates a large
maintenance migration.

### Emit JUnit XML and retain timing artefacts

The designated CI test workflow writes JUnit XML as an artefact. A timing
aggregation step consumes retained XML records to report duration summaries by
registered test class, initially as workflow output rather than a committed
repository artefact. Raw records retain their workflow retention period; the
format remains portable so aggregation may be replaced later.

Alternative considered: commit timing state to the repository. Rejected because
it creates noisy history and turns measurement output into merge-conflict-prone
source changes.

### Evaluate the experiment against explicit evidence

The trial records selected-test count, wall-clock duration, selector fallbacks,
and outcomes across ordinary commits. It remains enabled only if it materially
reduces commit feedback time without a selected-pass/full-PR-fail pattern
attributable to missed selection. A problem triggers clean reversion to the
current complete local pytest hook; a later `pytest-impacted` trial starts from
the same full-PR safety boundary.

## Risks / Trade-offs

- [Runtime dependency data is stale or absent] → seed it from a complete run and
  fall back conservatively when it cannot select safely.
- [Fixtures, plugins, templates, or external services escape import tracking] →
  configure broad-impact invalidators, retain full PR validation, and mark
  synchronisation/timing tests explicitly.
- [Testmon conflicts with coverage collection] → use a hook-specific no-coverage
  mode while preserving the complete coverage-enabled CI command.
- [Timing records create costly or noisy storage] → retain XML as bounded CI
  artefacts and publish summaries rather than committing raw data.
- [The experiment does not improve feedback time] → revert the hook and trial
  static import selection independently.

## Migration Plan

1. Register classes and produce the initial complete Testmon baseline.
2. Enable the local Testmon hook and record trial evidence while retaining full
   PR pytest execution.
3. Emit and aggregate JUnit timing evidence from the designated CI workflow.
4. Keep, tune, revert, or retry with `pytest-impacted` based on the recorded
   evidence. Reversion restores the previous complete local pytest hook and
   does not require changes to PR validation.
