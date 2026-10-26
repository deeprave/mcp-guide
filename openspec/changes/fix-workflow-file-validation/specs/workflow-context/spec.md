# Spec Delta

## MODIFIED Requirements

### Requirement: Workflow Bootstrap Guidance
The workflow monitoring system SHALL queue bootstrap guidance when a
workflow-enabled session starts. The guidance SHALL identify the configured
workflow file as a strict YAML mapping with lowercase keys, name `phase` as
required, and describe the supported optional fields and their value shapes.

#### Scenario: Missing workflow file bootstrap
- **WHEN** a workflow-enabled session starts and the configured workflow file does not exist
- **THEN** the guidance SHALL provide the strict workflow-file schema
- **AND** it SHALL instruct the agent to read the exact configured path directly rather than discover it through a glob, repository search, or tracked-file listing
- **AND** it SHALL instruct the agent to create the file when that direct read confirms it is absent, using `phase: discussion` when no other phase is selected
- **THEN** it SHALL describe `issue` as an optional dash-delimited phrase identifying current work, with no spaces and only filesystem-friendly characters
- **AND** it SHALL describe `plan` as an optional relative path to an existing plan document
- **AND** it SHALL describe `tracking` as an optional single-string external issue-tracker reference
- **AND** it SHALL state that `tracking` is not a mapping

#### Scenario: Existing workflow file bootstrap
- **WHEN** a workflow-enabled session starts and the configured workflow file exists
- **THEN** the guidance SHALL provide the strict workflow-file schema
- **AND** it SHALL instruct the agent to read and submit the complete configured file content
- **AND** it SHALL instruct the agent to read the exact configured path directly rather than discover it through a glob, repository search, or tracked-file listing

## ADDED Requirements

### Requirement: Exploration Phase Availability
Every enabled workflow configuration SHALL include the non-ordered
`exploration` phase. Explicit workflow lists that omit it SHALL have it added
without changing the order of the caller-supplied ordered phases.

#### Scenario: Explicit workflow list omits exploration
- **WHEN** an enabled workflow list is supplied without `exploration`
- **THEN** Guide SHALL add `exploration` to its effective phase list
- **AND** it SHALL preserve the order of the supplied phases

#### Scenario: Existing configuration omits exploration
- **WHEN** Guide reads an existing workflow list that omits `exploration`
- **THEN** Guide SHALL make `exploration` available in the effective workflow configuration
