# Purge Useless Tests

**Status**: Proposed
**Priority**: Medium
**Complexity**: Medium
**Recurrence**: Every 2 weeks

## Why

The test suite currently has 1738 tests taking ~76s. Over time, TDD scaffolding tests, duplicate coverage, framework-testing tests, and feature-presence checks accumulate. This slows CI, obscures real coverage gaps, and makes the suite harder to maintain.

This is a recurring housekeeping task, not a one-off.

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
5. Target: reduce test count by 20-30% while maintaining or improving real coverage
