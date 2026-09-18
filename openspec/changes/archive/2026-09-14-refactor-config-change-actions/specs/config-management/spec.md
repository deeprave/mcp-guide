## MODIFIED Requirements

### Requirement: Config File Change Detection
The system SHALL automatically detect configuration file modifications,
compare the validated current snapshot with the previous snapshot, and publish
one immutable configuration snapshot delta to the process runtime. ConfigManager
SHALL NOT register, select, or invoke Session instances.

#### Scenario: Config file modified
- **WHEN** a configuration file is modified on disk
- **THEN** the system validates and diffs the replacement snapshot against the
  cached snapshot
- **AND** publishes the old/new snapshots, global-flag change information, and
  changed strict project identities to the process runtime

#### Scenario: Multiple sessions active
- **WHEN** multiple sessions are active and a configuration file change affects
  more than one of their effective configurations
- **THEN** the process runtime selects each affected live bound session and
  delivers an independent scoped update
- **AND** unbound, expiring, and sessions for unrelated project identities
  receive no update
- **AND** failure reconciling one session does not affect others
