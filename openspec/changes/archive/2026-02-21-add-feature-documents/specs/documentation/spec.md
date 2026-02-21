## ADDED Requirements

### Requirement: Workflow Documentation
The documentation SHALL provide comprehensive coverage of workflow support features.

#### Scenario: User learns workflow phases
- **WHEN** user reads workflows.md
- **THEN** documentation explains discussion, planning, implementation, check, and review phases

#### Scenario: User configures workflow-consent
- **WHEN** user needs to configure workflow-consent
- **THEN** documentation provides precise configuration instructions

#### Scenario: User discovers prompt commands
- **WHEN** user wants to use workflow commands
- **THEN** documentation lists available default prompt commands

### Requirement: OpenSpec Documentation
The documentation SHALL provide comprehensive coverage of OpenSpec integration.

#### Scenario: User learns OpenSpec commands
- **WHEN** user reads openspec.md
- **THEN** documentation lists all available OpenSpec commands with descriptions

#### Scenario: User understands OpenSpec workflow
- **WHEN** user needs to use OpenSpec
- **THEN** documentation explains the interaction model and workflow phases

### Requirement: Consolidated Documentation Index
The documentation SHALL have a single index file at docs/index.md.

#### Scenario: User finds all documentation from single index
- **WHEN** user views docs/index.md
- **THEN** links to workflows.md and openspec.md are present

#### Scenario: No duplicate index files
- **WHEN** documentation is built
- **THEN** docs/user/INDEX.md does not exist
