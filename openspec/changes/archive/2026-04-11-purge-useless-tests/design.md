# Design: Purge Useless Tests

## Purpose

This change reduces the size, runtime, and maintenance burden of the test suite without weakening meaningful behavioral coverage.

The key design constraint is:

```text
remove low-signal tests
without removing tests that protect product behavior
```

and:

```text
optimize slow tests directly
when simple count reduction does not materially improve runtime
```

## Design Goals

1. Preserve tests that defend real application behavior
2. Remove tests that only restate framework or language behavior
3. Consolidate repetitive tests before deleting coverage wholesale
4. Use the current suite baseline to measure change
5. Keep integration, security, and state-transition coverage strong
6. Prefer targeted runtime improvements over broad pruning once the obvious low-value tests are gone

## Baseline

The current suite baseline for this change is:

- `1754` passing tests
- `74.27s` runtime for `uv run pytest -q`
- `84%` total coverage (`9028` statements, `1463` missed)
- `159` test files
- `95` unit-test files
- `24` integration-test files

These numbers should be used as the before-state when evaluating reductions.

## Runtime Optimization Strategy

Once the first low-signal reduction pass is complete, further work should be duration-driven.

This means:

- profile the full suite with pytest duration reporting
- identify the slowest individual tests and files
- reduce or eliminate avoidable waits, repeated bootstrapping, and expensive packaging work
- keep the same behavioral guarantee where possible, but choose cheaper ways to assert it

In this pass, that strategy was applied to:

- `tests/unit/scripts/test_mcp_guide_install.py`
  - replaced an expensive isolated-virtualenv installation check with a direct packaging-contract test that verifies the declared console-script target and invokes the mapped Click command
- `src/mcp_guide/file_lock.py` and related tests
  - introduced a configurable lock retry interval so tests can run with short polling while production keeps the default one-second retry

## Test Classification Model

This change should classify tests into three buckets:

### Keep

Tests that protect real behavior, including:

- end-to-end and integration flows
- workflow state transitions
- document store semantics
- security and path-handling behavior
- configuration and mutation behavior with meaningful invariants
- regressions for previously fixed bugs

### Consolidate

Tests that are valuable but overly repetitive, including:

- repeated invalid-input cases that can be parameterized
- near-identical tool tests that differ only by one field or option
- tiny files that belong naturally in a related module
- repeated fixture setup that can be shared

### Remove

Tests that no longer provide meaningful signal, including:

- framework-behavior tests for Python, pytest, asyncio, or third-party libraries
- duplicate tests asserting the same behavior with trivial input changes
- old TDD scaffolding that only reflects historical implementation details
- feature-presence tests that only assert a method, field, or class exists
- trivial field-storage tests with no invariants

## Audit Strategy

The suite should be audited in targeted batches rather than edited uniformly.

### First-pass audit targets

These files are the most likely to contain removable or heavily consolidatable tests:

- `tests/unit/test_mcp_guide/discovery/test_files.py`
- `tests/unit/test_mcp_core/test_validation.py`
- `tests/unit/test_mcp_guide/tools/test_tool_collection.py`
- `tests/unit/test_mcp_guide/tools/test_tool_category.py`
- `tests/unit/test_mcp_guide/tools/test_tool_project.py`
- `tests/test_template_functions.py`
- `tests/test_template_context_cache.py`
- `tests/unit/test_mcp_guide/test_uri_parser.py`

### Audit order

1. Remove obvious trivial or framework-oriented tests
2. Parameterize repetitive validator and tool tests
3. Merge tiny or overlapping test files where it improves clarity
4. Re-run the full suite and coverage after each batch
5. If runtime remains high, profile and optimize the slowest tests directly

## Scope Boundaries

This change should not:

- chase micro-optimizations in production code just to satisfy tests
- remove integration coverage to hit a target percentage
- reduce regression coverage for recently fixed bugs
- rewrite the whole suite structure in one pass

It may:

- add narrowly scoped test-only configurability to timing-sensitive production helpers when that preserves behavior and materially reduces test runtime
- replace an expensive test with a cheaper test that asserts the same contract more directly

The goal is to improve signal-to-noise, not to maximize deletion.

## Success Criteria

This change is successful when:

- the suite is materially smaller and easier to maintain
- repetitive tests are consolidated into clearer parameterized coverage
- low-value tests are removed with written rationale
- the full suite still passes
- meaningful coverage remains stable or improves on important paths

## Rationale

The suite already contains strong integration and behavioral coverage, so the best path is selective reduction rather than aggressive pruning. Concentrating first on trivial field tests, repetitive validators, and duplicated tool cases is the safest way to reduce cost while preserving confidence.

After that first pass, the runtime profile showed that the remaining cost was concentrated in a few hotspots rather than spread evenly across the suite. At that point, direct optimization of the slowest tests became the right design choice.
