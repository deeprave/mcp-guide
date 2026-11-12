# Proposal

## Why

The Python 3.13 CI job took about twice as long as the 3.14 and 3.15 jobs, but only Python 3.14 currently preserves per-test timing data. Comparable reports are needed to investigate whether the difference comes from particular tests, interpreter-version performance, dependency resolution, or hosted-runner variation. The observed result is not evidence that newer Python versions are necessarily faster: comparable work in other projects has shown runtimes increasing across successive Python versions.

## What Changes

- Generate JUnit timing data for every Python version in the test matrix.
- Upload each matrix entry's report as a clearly versioned CI artifact.
- Retain the full, unfiltered CI test suite for every supported Python version.
- Provide the evidence required for a subsequent, repeated-run investigation of cross-version timing differences.

## Capabilities

### New Capabilities

None. This is CI observability tooling and does not change a product capability.

### Modified Capabilities

None.

## Impact

- `.github/workflows/python-mcp-test.yml`
- CI artifact retention and test-duration diagnostics
