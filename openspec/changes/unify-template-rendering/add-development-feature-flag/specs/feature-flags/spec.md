# feature-flags Specification Delta

## ADDED Requirements

### Requirement: Development Mode Flag
The system SHALL provide a `guide-development` boolean feature flag to control development-specific behaviors.

#### Scenario: Development mode enabled
- GIVEN the `guide-development` flag is set to `true`
- WHEN command discovery runs
- THEN filesystem mtimes are checked on every execution
- AND command changes are detected automatically

#### Scenario: Production mode (flag disabled)
- GIVEN the `guide-development` flag is `false` or unset
- WHEN command discovery runs
- THEN cached command data is used without mtime checks
- AND directory traversal is skipped after initial scan

#### Scenario: Flag validation
- GIVEN a user attempts to set `guide-development` flag
- WHEN the value is not a boolean
- THEN the system rejects the value with a validation error
- AND provides guidance on valid values (true/false)
