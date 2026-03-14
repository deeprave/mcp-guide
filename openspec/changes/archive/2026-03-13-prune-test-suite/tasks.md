## 1. Baseline and Analysis
- [x] 1.1 Capture current coverage report (`coverage-before.txt`)
- [x] 1.2 Count current test files and test cases
- [x] 1.3 Identify tests matching removal criteria (coverage-only, duplicates, orphaned, private access, poor names)
- [x] 1.4 Create removal candidate list with rationale

## 2. Test Removal - Coverage-Only Tests
- [x] 2.1 Review and remove tests that only exist for coverage metrics
- [x] 2.2 Run test suite to verify remaining tests pass
- [x] 2.3 Check coverage hasn't dropped significantly
- [x] 2.4 Commit changes

## 3. Test Removal - Duplicate and Overlapping Tests
- [x] 3.1 Identify duplicate tests (identical behavior verification)
- [x] 3.2 Identify overlapping tests (similar behavior with variations)
- [x] 3.3 Consolidate or remove redundant tests
- [x] 3.4 Run test suite to verify remaining tests pass
- [x] 3.5 Check coverage hasn't dropped significantly
- [x] 3.6 Commit changes

## 4. Test Removal - Orphaned Tests
- [x] 4.1 Identify tests for code that no longer exists
- [x] 4.2 Remove orphaned tests
- [x] 4.3 Run test suite to verify remaining tests pass
- [x] 4.4 Check coverage hasn't dropped significantly
- [x] 4.5 Commit changes

## 5. Test Removal - Encapsulation Violations
- [x] 5.1 Identify tests accessing private internals
- [x] 5.2 Identify tests accessing dunder attributes
- [x] 5.3 Remove or refactor tests to use public interface
- [x] 5.4 Run test suite to verify remaining tests pass
- [x] 5.5 Check coverage hasn't dropped significantly
- [x] 5.6 Commit changes

## 6. Test Naming Improvements
- [x] 6.1 Identify tests with "coverage" or anti-pattern names
- [x] 6.2 Identify tests with unclear names
- [x] 6.3 Rename or remove tests as appropriate
- [x] 6.4 Run test suite to verify remaining tests pass
- [x] 6.5 Commit changes

## 7. TDD Scaffolding Evaluation
- [x] 7.1 Identify TDD scaffolding tests
- [x] 7.2 Evaluate each for ongoing regression value
- [x] 7.3 Remove tests without ongoing value
- [x] 7.4 Run test suite to verify remaining tests pass
- [x] 7.5 Check coverage hasn't dropped significantly
- [x] 7.6 Commit changes

## 8. Final Verification
- [x] 8.1 Run complete test suite with coverage
- [x] 8.2 Capture final coverage report (`coverage-after.txt`)
- [x] 8.3 Compare before/after coverage per module
- [x] 8.4 Count final test files and test cases
- [x] 8.5 Run linting and type checking
- [x] 8.6 Verify all quality checks pass
