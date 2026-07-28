## ADDED Requirements

### Requirement: Guide URL skill command registration
The system SHALL register the Guide URL skill command through the normal command discovery pipeline.

#### Scenario: Command discovery
- **WHEN** the command templates are discovered for a bound project
- **THEN** the Guide URL skill command SHALL be available with its arguments and agent requirements
