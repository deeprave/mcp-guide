## ADDED Requirements

### Requirement: Conservative direct filesystem confirmation
The system SHALL keep direct server-side filesystem access disabled until a session has been confirmed as a shared stdio filesystem session.

#### Scenario: HTTP(S) session
- **WHEN** a session uses HTTP or HTTPS transport
- **THEN** the system SHALL treat the client filesystem as unshared
- **AND** SHALL use agent-relay behavior for filesystem-derived data

#### Scenario: Unconfirmed stdio session
- **WHEN** a session uses stdio transport without successful confirmation
- **THEN** the system SHALL treat the client filesystem as unshared
- **AND** SHALL retain existing file-relay prompts and tools

#### Scenario: Confirmed stdio session
- **WHEN** a stdio session reports a project directory equal to the server's resolved working directory
- **AND** an initial ingest of the configured workflow file matches the server file's resolved path, size, and modification time
- **THEN** the system SHALL mark direct filesystem access confirmed for that session

### Requirement: Narrow direct access scope
The system SHALL limit confirmed direct filesystem reads to the confirmed project root and supported workflow and OpenSpec data.

#### Scenario: Direct workflow and OpenSpec reads
- **WHEN** direct filesystem access is confirmed
- **THEN** the system SHALL read the configured workflow file and OpenSpec metadata from the server filesystem
- **AND** SHALL apply existing path-security validation before each read
- **AND** SHALL not grant direct access outside the confirmed project root

#### Scenario: Confirmation invalidation
- **WHEN** root validation, direct file access, or freshness validation fails
- **THEN** the system SHALL revoke direct filesystem access for that session
- **AND** SHALL return to agent-relay behavior
