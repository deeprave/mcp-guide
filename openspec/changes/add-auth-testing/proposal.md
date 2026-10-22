# Proposal

## Why

The reference adapter has focused Guide tests and the independently developed
`auth-guide` service has its own tests, but neither proves that their published
interfaces work together. A repeatable black-box compatibility suite is needed
to detect integration, request-isolation, trust, and failure-boundary
regressions on the operating systems used for supported deployments.

## What Changes

- Add a cross-project, black-box compatibility test suite that starts real
  `auth-guide` and Guide HTTPS processes with disposable state.
- Exercise public account administration and token flows, then invoke Guide
  through an MCP client using ordinary, administrative, missing, and changed
  bearer evidence.
- Validate lazy provider availability, safe protected-operation failure, and
  trusted/untrusted TLS behaviour without adding a Guide-specific CA bypass.
- Run the suite in Linux and macOS CI; document Windows as deliberately
  deferred until a future change.
- Keep the suite out of normal unit-test execution while making it repeatable
  in supported development and CI environments.

## Capabilities

### New Capabilities
- `auth-provider-compatibility-testing`: Repeatable black-box verification of
  the published `auth-guide` service and Guide reference-adapter boundary.

### Modified Capabilities

- None.

## Impact

- Affects the test and CI configuration in this repository and the companion
  `auth-guide` repository.
- Requires test-only process orchestration, temporary directories/databases,
  ephemeral TLS material, and an MCP client.
- Does not alter Guide authentication semantics, add provider configuration, or
  weaken the operating-system trust-store boundary.
