## Context

The test suite has grown organically through TDD cycles and feature development. While this produced comprehensive coverage (82%, 1520 tests across 149 files), not all tests provide equal value. Some tests were scaffolding for TDD cycles, others exist purely for coverage metrics, and some test implementation details that should remain private.

The project follows strict guidelines (INSTRUCTIONS.md) about:
- Not testing private internals (especially dunder attributes)
- Not writing tests just for coverage
- Removing TDD scaffolding tests after refactoring
- Meaningful test names

This pruning effort aligns the test suite with these guidelines.

## Goals

1. **Reduce to focused tests** - Each test verifies specific behavior
2. **Remove duplication** - Consolidate overlapping tests
3. **Maintain coverage** - Keep ≥90% target (currently 82%)
4. **Improve maintainability** - Clearer intent, less code
5. **Enforce guidelines** - Align with INSTRUCTIONS.md

## Non-Goals

- Rewriting test framework or infrastructure
- Changing test organization structure
- Adding new test coverage
- Performance optimization of test execution

## Decisions

### Test Removal Criteria

**Remove if:**
1. Test only exists for coverage (no behavior verification)
2. Test duplicates another test's verification
3. Test verifies code that no longer exists
4. Test accesses private internals (violates encapsulation)
5. Test name contains "coverage" or similar anti-patterns
6. TDD scaffolding test with no ongoing regression value

**Keep if:**
1. Test verifies specific user-facing behavior
2. Test catches regressions in critical paths
3. Test documents expected behavior through examples
4. Test verifies edge cases or error conditions
5. Test is unique and focused

### Consolidation Strategy

When multiple tests verify similar behavior:
1. Identify the most comprehensive test
2. Ensure it covers all scenarios from redundant tests
3. Remove redundant tests
4. Update test name if needed for clarity

### Coverage Verification

Before pruning:
```bash
uv run pytest --cov=src --cov-report=term-missing > coverage-before.txt
```

After pruning:
```bash
uv run pytest --cov=src --cov-report=term-missing > coverage-after.txt
```

Compare line coverage per module. If coverage drops significantly (>5%) in any module, investigate whether removed tests were actually valuable.

## Alternatives Considered

### Alternative 1: Keep All Tests
**Rejected** - Violates project guidelines and creates maintenance burden

### Alternative 2: Mark Tests as "Coverage Only"
**Rejected** - Still requires maintenance, doesn't solve the problem

### Alternative 3: Separate Coverage Tests
**Rejected** - Tests should verify behavior, not exist for metrics

## Risks & Trade-offs

### Risk: Removing Valuable Regression Tests
**Likelihood**: Medium
**Impact**: High
**Mitigation**:
- Review each removal carefully
- Run full suite before/after
- Document significant removals
- Can restore from git history if needed

### Risk: Coverage Drop
**Likelihood**: Low
**Impact**: Medium
**Mitigation**:
- Current coverage is 82%, target is ≥90%
- Focused tests often improve coverage
- Monitor per-module coverage
- Add targeted tests if needed

### Trade-off: Time Investment
Reviewing 1520 tests takes time, but improves long-term maintainability and aligns with project standards.

## Migration Plan

1. **Baseline** - Capture current coverage and test count
2. **Identify** - Flag tests matching removal criteria
3. **Review** - Validate each flagged test
4. **Remove** - Delete tests in small batches
5. **Verify** - Run suite after each batch
6. **Document** - Record coverage changes
7. **Commit** - Incremental commits per batch

No user-facing changes. Internal test suite only.

## Open Questions

None - criteria and approach are clear.
