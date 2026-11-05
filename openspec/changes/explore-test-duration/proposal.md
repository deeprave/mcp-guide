# Proposal

## Why

The full pytest inventory makes every commit and push expensive, slowing feedback
despite its value for finding defects. The project needs a reversible way to run
only an affected subset at commit time without weakening the intentional full
pytest validation that protects pull requests.

## What Changes

- Introduce a local affected-test experiment for the pre-commit pytest hook,
  initially using `pytest-testmon` and retaining `pytest-impacted` as the
  fallback candidate if Testmon selection is insufficiently trustworthy or
  economical.
- Keep complete pytest runs as the required pull-request validation; affected
  selection is only an earlier feedback mechanism.
- Establish durable pytest markers for unit, integration, synchronisation,
  timing-dependent, and slow test classes, deriving unit and integration marks
  from the existing test hierarchy where practical.
- Add a workflow that emits JUnit XML timing data and accumulates it into a
  decision-supporting view of test duration classes.
- Define trial success, rollback, and retry criteria. The experiment may be
  reverted wholesale and need not ship as an individual commit or pull request.

## Capabilities

### New Capabilities

- `test-feedback-selection`: Select, classify, and measure tests for rapid local
  feedback while retaining complete pull-request validation.

### Modified Capabilities

None.

## Impact

- Affected configuration: `.pre-commit-config.yaml`, `pyproject.toml`, and
  GitHub Actions workflows.
- Likely development dependency trial: `pytest-testmon`; `pytest-impacted` is
  evaluated only as a fallback.
- Affected tests: test-location marker registration and any test metadata needed
  for synchronisation or timing-sensitive cases.
- No production MCP behaviour or public API changes.
