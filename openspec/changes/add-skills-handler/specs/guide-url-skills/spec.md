## ADDED Requirements

### Requirement: Project-scoped Guide skill packages
The system SHALL represent reusable project skills as packages containing `SKILL.md` and optional supporting members.

#### Scenario: Serve a skill package
- **WHEN** an agent requests a supported skill package for the current project
- **THEN** the system SHALL provide the package entrypoint and its available references, scripts, and assets through Guide
- **AND** the package content SHALL be rendered for the current project and Guide settings

### Requirement: Skill catalog discovery
The system SHALL provide a Guide skill catalog containing the metadata needed for an agent to select a skill.

#### Scenario: Inspect available skills
- **WHEN** an agent requests the skill catalog
- **THEN** the system SHALL list each available skill's identifier, description, and usage guidance
- **AND** SHALL identify the package entrypoint and available package members

### Requirement: Agent-native skill exchange
The system SHALL support optional import and project-scoped export of supported skill packages.

#### Scenario: Export a supported skill
- **WHEN** an agent requests export of a supported skill package and supports a configured project-local destination
- **THEN** the system SHALL materialise the resolved package in that destination using the agent's required metadata

#### Scenario: Reject unsupported exchange
- **WHEN** import or export receives an unsupported package, URL, agent, or collision
- **THEN** the system SHALL explain why the operation is unavailable
- **AND** SHALL NOT create a partial skill package
