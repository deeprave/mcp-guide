## MODIFIED Requirements

### Requirement: Additional Read Paths Configuration

The system SHALL support persisted absolute paths for user-configured additional read-only access outside project root. Runtime-derived read defaults SHALL be held only in the active session and SHALL NOT be added to or serialised with `additional_read_paths`.

#### Scenario: Absolute path validation

- **WHEN** additional_read_paths is configured in project
- **THEN** all paths must be absolute paths
- **AND** relative paths raise ValueError during validation
- **AND** paths are validated against system directory blacklist

#### Scenario: Additional read path access

- **WHEN** read operation is requested on configured additional path
- **THEN** access is granted if path is within additional_read_paths
- **AND** subdirectories of additional paths are accessible
- **AND** path traversal outside additional paths is blocked

#### Scenario: Additional read paths persistence

- **WHEN** project configuration is saved
- **THEN** user-configured additional_read_paths are included in configuration file
- **AND** paths are stored as absolute paths
- **AND** configuration can be loaded and validated correctly

#### Scenario: Runtime defaults remain session-local

- **WHEN** Guide derives read paths for a bound worktree session
- **THEN** those defaults SHALL be used for that session only
- **AND** SHALL not be persisted as additional_read_paths
