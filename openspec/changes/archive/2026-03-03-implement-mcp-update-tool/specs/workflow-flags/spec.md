## ADDED Requirements

### Requirement: Autoupdate Feature Flag
The system SHALL provide a global feature flag `autoupdate` that controls automatic update prompting at startup.

#### Scenario: Global flag only
- **WHEN** flag is set at global level
- **THEN** flag is accepted and stored
- **AND** flag value is boolean (true/false)

#### Scenario: Project-level flag rejected
- **WHEN** flag is set at project level
- **THEN** validation error is returned
- **AND** error message states "autoupdate must be global flag only"

#### Scenario: Flag resolution
- **WHEN** `McpUpdateTask` checks flag
- **THEN** only global flag value is considered
- **AND** project-level value (if present) is ignored
