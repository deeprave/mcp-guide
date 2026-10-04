# Proposal

## Why

`add-mcp-authentication` correctly identifies command resources and prompt commands as potential authorisation boundaries, but Guide commands principally render instructions for a client to perform separately protected tool operations. Adding a user-scope gate without establishing a direct server-side mutation would unnecessarily prevent unauthenticated callers from using help, inspection, and onboarding guidance.

The completed exploration found no command-rendering path that directly performs a protected mutation. On 2026-10-04, the user approved closing this change without implementation or additional tests. Existing tool authorisation remains the enforcement boundary.

## What Changes

- Record the completed audit of shared command dispatch, rendering, elicitation and command-specific work.
- Retain existing unauthenticated command rendering and scoped tool enforcement unchanged.
- Withdraw the proposed prompt and command-URI spec deltas: no new runtime behaviour or command scope mechanism is needed.
- Close the implementation and additional-test tasks as unnecessary under the approved audit-only outcome.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- None. The audit confirms existing behaviour; no canonical specification changes require syncing.

## Impact

- Change artefacts only; no production code, tests, ADR or canonical specifications are modified by this closure.
- No authentication provider, command policy registry, decorator parameter or template-configurable access policy is introduced.
- The existing export permission side effect remains assigned to `retire-export-metadata`, not this change.
