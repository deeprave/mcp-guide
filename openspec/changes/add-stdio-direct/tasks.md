## 1. Direct-access state and confirmation

- [ ] 1.1 Add a session-scoped direct-filesystem state model that defaults to unconfirmed for every transport.
- [ ] 1.2 Add transport-aware eligibility so HTTP(S) stays relay-only and stdio starts unconfirmed.
- [ ] 1.3 Add the confirmation handshake using resolved client/server project roots and initial workflow-file path, size, and mtime agreement.
- [ ] 1.4 Apply path-security validation and invalidate confirmation on root, freshness, or direct-read failure.

## 2. Direct data sources

- [ ] 2.1 Write failing tests for unconfirmed stdio and HTTP(S) retaining relay behavior.
- [ ] 2.2 Implement direct workflow-file loading and semantic change processing after confirmation.
- [ ] 2.3 Implement direct OpenSpec CLI version, project, and change discovery after confirmation.
- [ ] 2.4 Write tests for confirmed reads, direct-read failures, and transition back to relay behavior.

## 3. Source-aware guidance

- [ ] 3.1 Expose confirmed direct-data availability to workflow and OpenSpec rendering.
- [ ] 3.2 Suppress relay prompts, text, and reminders only after the corresponding direct data is current.
- [ ] 3.3 Add tests that confirm suppressed relay guidance in direct mode and preserved guidance in every fallback mode.

## 4. Validation

- [ ] 4.1 Add focused tests for path validation, session isolation, and timestamp-resolution edge cases.
- [ ] 4.2 Run the relevant workflow, OpenSpec, transport, and template test groups.
- [ ] 4.3 Run Ruff, Ty, full pytest, and pre-commit checks.
