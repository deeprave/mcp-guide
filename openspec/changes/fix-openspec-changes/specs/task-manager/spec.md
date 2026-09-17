## ADDED Requirements

### Requirement: Passive OpenSpec project initialisation
The OpenSpec task SHALL establish CLI availability, version, and project
structure independently of collecting project change data. Detecting an
OpenSpec project SHALL NOT itself queue an OpenSpec changes-list instruction.

#### Scenario: OpenSpec project detection
- **WHEN** an enabled project's OpenSpec directory has been verified
- **THEN** the task SHALL retain the verified project state
- **AND** SHALL NOT request `openspec list --json` until a consumer requires
  changes data
