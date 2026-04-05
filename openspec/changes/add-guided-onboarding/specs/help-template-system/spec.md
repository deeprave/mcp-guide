## ADDED Requirements

### Requirement: Guided Onboarding Experience

The system SHALL provide a guided onboarding experience for project configuration.

#### Scenario: Initial onboarding guides user through setup
- **WHEN** a user begins onboarding for a project
- **THEN** the system guides them through relevant configuration choices
- **AND** it presents those choices in user-facing terms rather than requiring prior knowledge of internal configuration structures

#### Scenario: Onboarding supports later reconfiguration
- **WHEN** a user wants to revise project setup after initial onboarding
- **THEN** the same guided approach can be used to review and adjust existing configuration choices

### Requirement: Project-Aware Guidance

The onboarding flow SHALL inspect the project when possible and ask the user when project signals are insufficient.

#### Scenario: Project characteristics inform onboarding choices
- **WHEN** the project contains recognizable language, framework, or toolchain signals
- **THEN** onboarding uses those signals to prioritize relevant setup questions

#### Scenario: Ambiguous or missing project context falls back to user questions
- **WHEN** project inspection is ambiguous or unavailable
- **THEN** onboarding asks the user for the missing information before applying configuration
