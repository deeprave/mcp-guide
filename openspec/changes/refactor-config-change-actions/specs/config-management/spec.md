## MODIFIED Requirements

### Requirement: Config File Change Detection
The system SHALL automatically detect configuration file modifications,
compare the validated current snapshot with the previous snapshot, and publish
scoped effective configuration updates to active affected sessions.

#### Scenario: Config file modified
- **WHEN** a configuration file is modified on disk
- **THEN** the system validates and diffs the replacement snapshot against the
  cached snapshot
- **AND** each active session whose effective global or active-project
  configuration changed receives its scoped configuration update

#### Scenario: Multiple sessions active
- **WHEN** multiple sessions are active and a configuration file change affects
  more than one of their effective configurations
- **THEN** each affected session receives an independent scoped update
- **AND** sessions not affected by the change receive no update
- **AND** failure in one session callback does not affect others
