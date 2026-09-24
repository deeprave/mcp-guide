# Spec Delta

## Purpose

Provide explicit, opt-in guidance for agents to maintain concise current
handoff context without imposing project workflow conventions by default.

## ADDED Requirements

### Requirement: Handoff-context feature flag controls proactive guidance
The system SHALL resolve `handoff-context` through the normal project-then-global
feature-flag hierarchy. An absent or false effective value SHALL disable
proactive handoff-context update requests. The flag SHALL use the established
feature-flag registration, validation, and normalisation path, accept a
boolean-like value or non-empty target string, and be available globally and
per project. A user MAY still directly instruct an agent to prepare handoff
context while the flag is disabled.

#### Scenario: Default configuration does not request handoff context
- **WHEN** no effective `handoff-context` value is enabled
- **THEN** the TaskManager SHALL queue rendered guidance that no handoff
  context is configured for the current project
- **AND** the guidance SHALL NOT request a handoff file update

#### Scenario: Project flag overrides global configuration
- **WHEN** a global `handoff-context` value is configured and a project configures its own value
- **THEN** the system SHALL use the project value for that project
- **AND** other projects without an override SHALL continue to use the global value

#### Scenario: Onboarding configures a project handoff preference
- **WHEN** guided onboarding reaches the optional handoff-context selection
- **THEN** it SHALL offer disabled, default, and custom project-target choices
- **AND** it SHALL map them respectively to `false`, `true`, and a validated
  project-relative target through the project feature-flag configuration path
- **AND** it SHALL recommend `.gitignore` coverage for enabled targets without
  requiring it

### Requirement: Enabled values select a handoff target
When the effective `handoff-context` value is `true`, the system SHALL request
updates to `context.json` under `{{paths.documents}}`. When it is a filename,
the system SHALL request updates to that filename under `{{paths.documents}}`.
When it is a relative file path, the system SHALL request updates to that
resolved project path. An absolute path SHALL be rejected.

#### Scenario: Boolean enablement uses the default target
- **WHEN** `handoff-context` is true
- **THEN** startup guidance SHALL identify `{{paths.documents}}/context.json` as the target
- **AND** it SHALL request an updated and current handoff context

#### Scenario: Filename selects a document-directory target
- **WHEN** `handoff-context` contains a filename without directory components
- **THEN** startup guidance SHALL identify that filename beneath `{{paths.documents}}`
- **AND** it SHALL request an updated and current handoff context

#### Scenario: Relative path selects an explicit target
- **WHEN** `handoff-context` contains a relative path with directory components
- **THEN** startup guidance SHALL identify the resolved relative target
- **AND** it SHALL not relocate that target beneath `{{paths.documents}}`

#### Scenario: Absolute path is rejected
- **WHEN** a caller sets `handoff-context` to an absolute path
- **THEN** feature-flag validation SHALL reject the value

### Requirement: Handoff guidance matches the selected file format
The system SHALL request a format appropriate to the selected target's filename
extension. It SHALL request JSON for `.json`, Markdown for `.md`, plain text
for `.txt`, and the correspondingly implied format for other recognised
extensions.

#### Scenario: JSON target receives JSON guidance
- **WHEN** the selected target has a `.json` extension
- **THEN** startup guidance SHALL request current handoff context in valid JSON

#### Scenario: Markdown target receives Markdown guidance
- **WHEN** the selected target has a `.md` extension
- **THEN** startup guidance SHALL request current handoff context in Markdown

### Requirement: Handoff target must pass project write policy
Before requesting an update, the system SHALL resolve the selected relative
target and validate it with the project's existing
`ReadWriteSecurityPolicy.validate_write_path` against `allowed_write_paths`.
It SHALL not request an update for a path that fails that validation.

#### Scenario: Allowed project target is eligible
- **WHEN** the selected target passes the project's existing write policy
- **THEN** the system SHALL include the handoff update request in startup guidance

#### Scenario: Disallowed target is omitted
- **WHEN** the selected target does not pass the project's existing write policy
- **THEN** the system SHALL omit the handoff update request
- **AND** it SHALL not direct the agent to create or modify that path

### Requirement: StartupTask queues rendered handoff guidance
The TaskManager-owned `StartupTask` SHALL evaluate handoff-context delivery
alongside its existing documentation-update checks. It SHALL resolve the
effective handoff-context value, render a dedicated system template, and
queue the resulting agent instruction. It SHALL NOT duplicate the handoff
delivery in a separate task or hard-code its agent-facing wording.

#### Scenario: Disabled guidance is rendered and queued
- **WHEN** `StartupTask` evaluates a project with `handoff-context` absent,
  null, or false
- **THEN** it SHALL render and queue the disabled handoff-context template

#### Scenario: Enabled guidance is rendered and queued
- **WHEN** `StartupTask` evaluates a project with an eligible resolved handoff
  target
- **THEN** it SHALL render and queue the enabled handoff-context template
- **AND** the rendered guidance SHALL identify the resolved target and its
  requested format
