# Prune Test Suite

**Status**: Proposed  
**Priority**: Medium  
**Complexity**: Medium

## Why

The test suite has grown to 149 test files with 1520 test cases and 82% coverage. While comprehensive, it contains tests that don't provide meaningful value:

- Tests that only exist to achieve coverage metrics rather than verify behavior
- Duplicate or overlapping tests that could be consolidated
- Tests for code that no longer exists (orphaned tests)
- Tests that expose and verify internal implementation details
- Tests with poor naming that don't communicate intent
- TDD scaffolding tests that served their purpose during development but aren't valuable for regression

This creates maintenance burden, slower test execution, and makes it harder to identify which tests actually matter.

## What Changes

**Test Quality Improvements:**
- Remove tests that only exist for coverage metrics (no behavioral verification)
- Consolidate duplicate and overlapping tests
- Remove tests for deleted/obsolete code
- Remove or refactor tests that access private internals (violates encapsulation guidelines)
- Rename or remove tests with poor names (e.g., containing "coverage")
- Evaluate TDD scaffolding tests for ongoing value

**Verification:**
- Maintain ≥90% coverage target (currently 82%, may improve with focused tests)
- Document coverage before/after pruning
- Ensure all remaining tests verify actual behavior
- All remaining tests must pass

**Affected Components:**
- All test files under `tests/` directory
- Test configuration in `pyproject.toml` and `.coveragerc`

## Impact

**Benefits:**
- Faster test execution (fewer tests to run)
- Clearer test intent (each test has clear purpose)
- Easier maintenance (less test code to update)
- Better signal-to-noise ratio (failures indicate real issues)
- Improved adherence to project guidelines (INSTRUCTIONS.md)

**Risks:**
- May accidentally remove valuable regression tests
- Coverage percentage might temporarily drop
- Need careful review to distinguish valuable vs. redundant tests

**Mitigation:**
- Review each test removal decision
- Run full test suite before and after
- Verify coverage metrics
- Document rationale for significant removals
