## ADDED Requirements

### Requirement: Project-scoped Guide URL skill creation
The system SHALL provide a command that creates a reusable skill for the current project from supported Guide URL content.

#### Scenario: Create a supported skill
- **WHEN** an agent invokes the skill command with a supported Guide URL and supported agent context
- **THEN** the system SHALL create the skill in that agent's project-scoped skill location
- **AND** the skill SHALL contain the resolved Guide content and required agent metadata

#### Scenario: Reject unsupported input
- **WHEN** the command receives an unsupported URL or unsupported agent
- **THEN** the system SHALL explain why creation is unavailable
- **AND** SHALL NOT create a partial skill file
