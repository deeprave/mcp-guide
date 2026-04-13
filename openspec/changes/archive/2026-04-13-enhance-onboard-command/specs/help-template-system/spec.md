## MODIFIED Requirements

### Requirement: Guided Onboarding Experience

The system SHALL provide a guided onboarding experience for project configuration.

#### Scenario: Initial onboarding guides user through setup
- **WHEN** a user begins onboarding for a project
- **THEN** the system guides them through relevant configuration choices
- **AND** it presents those choices in user-facing terms rather than requiring prior knowledge of internal configuration structures

#### Scenario: Onboarding supports later reconfiguration
- **WHEN** a user wants to revise project setup after initial onboarding
- **THEN** the same guided approach can be used to review and adjust existing configuration choices

#### Scenario: Onboarding summarizes current configuration before questioning
- **WHEN** onboarding begins
- **THEN** it summarizes the dimensions that are already configured before asking the first onboarding question

#### Scenario: Onboarding asks one question at a time
- **WHEN** onboarding needs user input for a remaining configuration dimension
- **THEN** it asks exactly one onboarding question at a time
- **AND** it waits for the user's response before asking the next onboarding question

#### Scenario: Clarifying questions are allowed during onboarding
- **WHEN** the user asks a clarifying question instead of answering the current onboarding question
- **THEN** onboarding answers the clarification
- **AND** resumes from the current onboarding dimension afterward

### Requirement: Project-Aware Guidance

The onboarding flow SHALL inspect existing guide configuration and project signals when possible, and ask the user when those signals are insufficient.

#### Scenario: Existing guide configuration informs onboarding choices
- **WHEN** onboarding begins
- **THEN** it inspects the current guide configuration before asking questions
- **AND** uses `guide://_project?verbose` as the primary source of current project/category state, including the `policies` category
- **AND** inspects project flags including `onboarded`, `workflow`, and `openspec`
- **AND** inspects available profiles before asking about language or framework profiles

#### Scenario: Project characteristics inform onboarding defaults
- **WHEN** the project contains recognizable language, framework, or toolchain signals
- **THEN** onboarding uses those signals to prioritize relevant setup questions
- **AND** proposes likely defaults when they can be inferred from the inspected state

#### Scenario: Fully configured dimensions are skipped silently
- **WHEN** a configuration dimension is already fully configured
- **THEN** onboarding does not ask the user about that dimension again

#### Scenario: Partially configured dimensions are revisited
- **WHEN** a configuration dimension is only partially configured
- **THEN** onboarding mentions the current state
- **AND** asks the user whether to confirm or adjust it

#### Scenario: Ambiguous or missing project context falls back to user questions
- **WHEN** project inspection or existing configuration is ambiguous or unavailable
- **THEN** onboarding asks the user for the missing information before applying configuration
