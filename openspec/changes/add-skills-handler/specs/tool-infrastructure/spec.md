## ADDED Requirements

### Requirement: Skill package command registration
The system SHALL register skill import and export commands through the normal command discovery pipeline.

#### Scenario: Skill command discovery
- **WHEN** the command templates are discovered for a bound project
- **THEN** the supported skill exchange commands SHALL be available with their arguments and agent requirements
