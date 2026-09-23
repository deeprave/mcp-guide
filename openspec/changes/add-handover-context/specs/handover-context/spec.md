# Spec Delta

## Purpose

Provide explicit, opt-in guidance for agents to maintain concise current
handover context without imposing project workflow conventions by default.

## ADDED Requirements

### Requirement: Handoff-context feature flag controls proactive guidance
The system SHALL resolve `handoff-context` through the normal project-then-global
feature-flag hierarchy. An absent or false effective value SHALL disable
proactive handover-context guidance. A user MAY still directly instruct an
agent to prepare handover context while the flag is disabled.

#### Scenario: Default configuration does not request handover context
- **WHEN** no effective `handoff-context` value is enabled
- **THEN** milestone responses SHALL omit any request to create or update handover context
- **AND** the response SHALL not imply that a handover file is required

#### Scenario: Project flag overrides global configuration
- **WHEN** a global `handoff-context` value is configured and a project configures its own value
- **THEN** the system SHALL use the project value for that project
- **AND** other projects without an override SHALL continue to use the global value

### Requirement: Enabled values select a handover target
When the effective `handoff-context` value is `true`, the system SHALL request
updates to `context.json` under `{{paths.documents}}`. When it is a filename,
the system SHALL request updates to that filename under `{{paths.documents}}`.
When it is a relative file path, the system SHALL request updates to that
resolved project path.

#### Scenario: Boolean enablement uses the default target
- **WHEN** `handoff-context` is true
- **THEN** milestone guidance SHALL identify `{{paths.documents}}/context.json` as the target
- **AND** it SHALL request an updated and current handover context

#### Scenario: Filename selects a document-directory target
- **WHEN** `handoff-context` contains a filename without directory components
- **THEN** milestone guidance SHALL identify that filename beneath `{{paths.documents}}`
- **AND** it SHALL request an updated and current handover context

#### Scenario: Relative path selects an explicit target
- **WHEN** `handoff-context` contains a relative path with directory components
- **THEN** milestone guidance SHALL identify the resolved relative target
- **AND** it SHALL not relocate that target beneath `{{paths.documents}}`

### Requirement: Handover guidance matches the selected file format
The system SHALL request a format appropriate to the selected target's filename
extension. It SHALL request JSON for `.json`, Markdown for `.md`, plain text
for `.txt`, and the correspondingly implied format for other recognised
extensions.

#### Scenario: JSON target receives JSON guidance
- **WHEN** the selected target has a `.json` extension
- **THEN** milestone guidance SHALL request current handover context in valid JSON

#### Scenario: Markdown target receives Markdown guidance
- **WHEN** the selected target has a `.md` extension
- **THEN** milestone guidance SHALL request current handover context in Markdown

### Requirement: Handover target must be writable within project policy
Before requesting an update, the system SHALL resolve the selected target and
confirm it is within the project root or covered by the project's existing
`allowed_write_paths` policy. It SHALL not request an update for a path that
fails that validation.

#### Scenario: Project-local target is eligible
- **WHEN** the selected target resolves within the project root
- **THEN** the system SHALL include the handover update request at a milestone

#### Scenario: Configured write target is eligible
- **WHEN** the selected target matches an `allowed_write_paths` entry
- **THEN** the system SHALL include the handover update request at a milestone

#### Scenario: Disallowed target is omitted
- **WHEN** the selected target is outside the project root and is not covered by `allowed_write_paths`
- **THEN** the system SHALL omit the handover update request
- **AND** it SHALL not direct the agent to create or modify that path
