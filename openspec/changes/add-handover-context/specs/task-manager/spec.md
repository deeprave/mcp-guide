## REMOVED Requirements

### Requirement: MCP Update Task

**Reason**: The startup task now delivers more than documentation-update
guidance, so its name must describe its broader responsibility.

## ADDED Requirements

### Requirement: Startup Task
The system SHALL provide `StartupTask` that checks the `autoupdate` feature
flag once at startup and queues an update instruction when enabled. It SHALL
also queue any applicable rendered project-specific startup guidance.

#### Scenario: Autoupdate enabled by default
- **WHEN** task initializes via startup timer
- **AND** `autoupdate` is not set
- **THEN** the update instruction is queued
- **AND** task unsubscribes after handling the startup check

#### Scenario: Autoupdate explicitly enabled
- **WHEN** task initializes via startup timer
- **AND** `autoupdate` feature flag is true
- **THEN** the update instruction is queued
- **AND** task unsubscribes after handling the startup check

#### Scenario: Autoupdate explicitly disabled
- **WHEN** task initializes via startup timer
- **AND** `autoupdate` feature flag is false
- **THEN** no update instruction is queued
- **AND** task unsubscribes after handling the startup check

#### Scenario: Prompt is tracked for acknowledgement
- **WHEN** task queues the update instruction
- **THEN** it is queued as an acknowledged instruction
- **AND** the task manager may re-send reminders until it is acknowledged

#### Scenario: Update acknowledgement stops reminders
- **WHEN** the agent runs `update_documents`
- **AND** `StartupTask` has a tracked instruction id
- **THEN** that instruction is acknowledged
- **AND** further reminders are not sent for the same queued prompt
