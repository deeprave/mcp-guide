## ADDED Requirements

### Requirement: Template Context Hierarchy
The template context system SHALL provide hierarchical variable resolution with OpenSpec integration when available.

#### Scenario: Context hierarchy with OpenSpec data
- **WHEN** OpenSpec support is enabled AND template context is computed
- **THEN** context hierarchy includes: file > category > collection > project > openspec > agent > system

#### Scenario: OpenSpec project data in context
- **WHEN** OpenSpec project is detected AND template is rendered
- **THEN** openspec context level contains project metadata, active changes, and spec domains

#### Scenario: Template rendering with OpenSpec variables
- **WHEN** template contains OpenSpec variables like {{openspec.project.name}}
- **THEN** variables are resolved from OpenSpec project metadata

#### Scenario: Context hierarchy without OpenSpec
- **WHEN** OpenSpec support is disabled OR no OpenSpec project detected
- **THEN** context hierarchy remains: file > category > collection > project > agent > system

## ADDED Requirements

### Requirement: OpenSpec Context Data
The template context system SHALL include OpenSpec project data when OpenSpec support is enabled.

#### Scenario: OpenSpec project metadata
- **WHEN** OpenSpec project is detected
- **THEN** context includes project name, description, and tech stack from openspec/project.md

#### Scenario: Active changes data
- **WHEN** OpenSpec project has active changes
- **THEN** context includes list of change IDs, titles, and status

#### Scenario: Specification domains
- **WHEN** OpenSpec project has specifications
- **THEN** context includes list of spec domains and descriptions

#### Scenario: Agent configuration
- **WHEN** AGENTS.md exists in OpenSpec project
- **THEN** context includes AI assistant configuration and conventions
