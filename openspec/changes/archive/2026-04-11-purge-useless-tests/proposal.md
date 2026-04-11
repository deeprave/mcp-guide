# Purge Useless Tests

**Status**: Proposed
**Priority**: Medium
**Complexity**: Medium
**Recurrence**: Every 2 weeks

## Why

The current suite baseline was:

- `1754` passing tests
- `74.27s` full runtime
- `84%` total coverage
- `159` test files, including `95` unit-test files and `24` integration-test files

Over time, TDD scaffolding tests, duplicate coverage, framework-testing tests, and feature-presence checks accumulate. This slows CI, obscures real coverage gaps, and makes the suite harder to maintain.

This is a recurring housekeeping task, not a one-off. In this pass, the work also expanded from low-signal test removal into targeted runtime reduction for the slowest remaining tests.

## What to Remove

- **Framework tests**: tests that verify Python, pytest, asyncio, or third-party library behaviour rather than our code
- **Duplicate coverage**: multiple tests asserting the same behaviour with trivially different inputs
- **TDD scaffolding**: red-green-refactor tests that served their purpose during development but now test implementation details of code that has since been refactored
- **Feature presence/removal tests**: tests that assert a function exists, a class has an attribute, or a removed feature is gone
- **Trivial tests**: tests that assert obvious things (e.g. constructor sets a field, `__repr__` returns a string)

## What to Consolidate

- Tests with identical patterns but different inputs → `@pytest.mark.parametrize`
- Near-duplicate test classes that could share fixtures
- Test files with only 1-2 tests that belong in a related file

## Approach

1. Audit each test directory (`tests/unit/`, `tests/integration/`)
2. Flag candidates with rationale
3. Remove or parametrize in batches
4. Verify coverage doesn't drop on meaningful code paths
5. Target: reduce test count where it improves signal-to-noise, and reduce full-suite runtime by addressing the slowest tests directly while maintaining or improving real coverage

## Baseline

The current baseline should be treated as the starting point for this change:

- `uv run pytest -q`
  - `1754 passed in 74.27s`
- coverage summary
  - `TOTAL 9028 statements`
  - `1463 missed`
  - `84%` covered

## Outcome

This pass achieved both quality and duration improvements:

- `1759 passed in 53.41s`
- `84%` total coverage
- `1759` collected tests, up slightly from the original baseline as other change work added targeted regression coverage during the same period

The strongest runtime wins came from:

- replacing an expensive throwaway-virtualenv console-script test with a cheaper packaging-contract test
- making lock retry timing test-configurable so concurrency tests no longer wait on one-second polling
- suppressing watcher startup in collection/category integration tests that do not exercise watcher behavior
- replacing repeated `switch_project()`-based test setup with direct bound sessions in shared helpers and high-churn unit/integration fixtures
- shortening artificial waits in `path_watcher` tests and narrowing several setup-heavy integration paths

Remaining runtime work, if needed later, should focus on the current slowest integration tests rather than further low-value unit-test pruning. The main remaining hotspots are:
- `tests/integration/test_tool_registration.py::test_mcp_client_can_initialize_and_list_tools`

The final checked worktree is slower than the lowest experimental timing reached during development because follow-up fixes restored stronger coverage boundaries, brought back an isolated packaging smoke test, and removed a risky production behavior shortcut. The remaining tail is now dominated by intentional integration work rather than broad avoidable test overhead.
