## MODIFIED Requirements

### Requirement: Feature Flag Runtime Changes

Feature flags SHALL take effect immediately on the next request after being set, without requiring server restart or manual cache clearing.

#### Scenario: Global flag change takes immediate effect
- **WHEN** a global feature flag is set via `set_feature_flag` tool
- **AND** a content request is made immediately after
- **THEN** the new flag value SHALL be used for that request

#### Scenario: Flag changes visible across sessions
- **WHEN** a global feature flag is changed in one session
- **AND** a content request is made in a different session
- **THEN** the new flag value SHALL be used

#### Scenario: Content format flag applies MIME formatting
- **WHEN** `content-format` flag is set to `mime`
- **AND** content with multiple files is requested
- **THEN** response SHALL include MIME multipart headers and boundaries

### Requirement: Feature Flag Error Handling

Feature flag resolution errors SHALL be logged with sufficient detail to diagnose issues, not silently swallowed.

#### Scenario: Flag resolution failure is logged
- **WHEN** feature flag resolution fails with an exception
- **THEN** the exception SHALL be logged with context
- **AND** a default value SHALL be returned
- **AND** the error SHALL not crash the request

#### Scenario: Bare exception handlers replaced
- **WHEN** reviewing flag resolution code
- **THEN** bare `except Exception` handlers SHALL be replaced with specific exception types
- **OR** SHALL include logging before returning default values
