## Why

Reducing full-suite runtime is the primary objective. The suite has grown beyond
2,000 tests, increasing the feedback time for every
change while retaining redundant, implementation-coupled, and temporary TDD
coverage. Maintaining a smaller suite focused on observable Guide behaviour
will make development faster and failures more informative.

## What Changes

- Audit every test module against its production behaviour and remove tests
  that are redundant, temporary TDD scaffolding, framework behaviour checks,
  existence checks, application-compatibility or legacy-state coverage,
  or implementation-detail assertions without regression value. Retain MCP
  protocol-version compatibility coverage, including legacy protocol clients.
- Remove tests for removed features, tools, classes and functions after checking
  the current production surface.
- Fold redundant single-behaviour tests and temporary TDD checks into more
  comprehensive behavioural scenarios, avoiding repeated setup and execution.
- Consolidate equivalent scenarios into readable parametrised tests where they
  share setup and assertions.
- Group related tests into coherent units where this improves navigation,
  while retaining independent tests when their setup or observable behaviour
  differs.
- Replace implementation-coupled mock assertions with behavioural assertions
  or lightweight real substitutes where practical.
- Preserve regression coverage for every supported public contract and verify
  the reduced suite in full.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

This is test-suite maintenance only; it does not alter Guide's public
behavioural requirements.

## Impact

- Affected area: the complete `tests/` suite, shared fixtures, and test-only
  helpers.
- No public API, runtime behaviour, dependency, or configuration changes.
- Success is measured by reduced full-suite runtime with retained current
  behavioural and MCP protocol coverage, not merely fewer test functions.
