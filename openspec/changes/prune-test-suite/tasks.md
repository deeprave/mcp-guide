## 1. Baseline and Analysis
- [ ] 1.1 Capture current coverage report (`coverage-before.txt`)
- [ ] 1.2 Count current test files and test cases
- [ ] 1.3 Identify tests matching removal criteria (coverage-only, duplicates, orphaned, private access, poor names)
- [ ] 1.4 Create removal candidate list with rationale

## 2. Test Removal - Coverage-Only Tests
- [ ] 2.1 Review and remove tests that only exist for coverage metrics
- [ ] 2.2 Run test suite to verify remaining tests pass
- [ ] 2.3 Check coverage hasn't dropped significantly
- [ ] 2.4 Commit changes

## 3. Test Removal - Duplicate and Overlapping Tests
- [ ] 3.1 Identify duplicate tests (identical behavior verification)
- [ ] 3.2 Identify overlapping tests (similar behavior with variations)
- [ ] 3.3 Consolidate or remove redundant tests
- [ ] 3.4 Run test suite to verify remaining tests pass
- [ ] 3.5 Check coverage hasn't dropped significantly
- [ ] 3.6 Commit changes

## 4. Test Removal - Orphaned Tests
- [ ] 4.1 Identify tests for code that no longer exists
- [ ] 4.2 Remove orphaned tests
- [ ] 4.3 Run test suite to verify remaining tests pass
- [ ] 4.4 Check coverage hasn't dropped significantly
- [ ] 4.5 Commit changes

## 5. Test Removal - Encapsulation Violations
- [ ] 5.1 Identify tests accessing private internals
- [ ] 5.2 Identify tests accessing dunder attributes
- [ ] 5.3 Remove or refactor tests to use public interface
- [ ] 5.4 Run test suite to verify remaining tests pass
- [ ] 5.5 Check coverage hasn't dropped significantly
- [ ] 5.6 Commit changes

## 6. Test Naming Improvements
- [ ] 6.1 Identify tests with "coverage" or anti-pattern names
- [ ] 6.2 Identify tests with unclear names
- [ ] 6.3 Rename or remove tests as appropriate
- [ ] 6.4 Run test suite to verify remaining tests pass
- [ ] 6.5 Commit changes

## 7. TDD Scaffolding Evaluation
- [ ] 7.1 Identify TDD scaffolding tests
- [ ] 7.2 Evaluate each for ongoing regression value
- [ ] 7.3 Remove tests without ongoing value
- [ ] 7.4 Run test suite to verify remaining tests pass
- [ ] 7.5 Check coverage hasn't dropped significantly
- [ ] 7.6 Commit changes

## 8. Final Verification
- [ ] 8.1 Run complete test suite with coverage
- [ ] 8.2 Capture final coverage report (`coverage-after.txt`)
- [ ] 8.3 Compare before/after coverage per module
- [ ] 8.4 Verify coverage ≥90% overall
- [ ] 8.5 Count final test files and test cases
- [ ] 8.6 Document coverage changes and test count reduction
- [ ] 8.7 Run linting and type checking
- [ ] 8.8 Verify all quality checks pass

## 9. Documentation
- [ ] 9.1 Document significant test removals and rationale
- [ ] 9.2 Update any test documentation if needed
- [ ] 9.3 Create summary of pruning results (tests removed, coverage impact)
