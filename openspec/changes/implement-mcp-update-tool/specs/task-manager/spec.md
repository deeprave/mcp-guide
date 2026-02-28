## ADDED Requirements

### Requirement: MCP Update Task
The system SHALL provide `McpUpdateTask` that checks the `autoupdate` feature flag once at startup and queues an instruction if enabled.

#### Scenario: Autoupdate enabled
- **WHEN** task initializes via `on_init()`
- **AND** `autoupdate` feature flag is true
- **THEN** instruction is queued from template (no acknowledgment required)
- **AND** task unsubscribes from TaskManager

#### Scenario: Autoupdate disabled
- **WHEN** task initializes via `on_init()`
- **AND** `autoupdate` feature flag is false or not present
- **THEN** task unsubscribes from TaskManager immediately
- **AND** no instruction is queued

#### Scenario: One-shot execution
- **WHEN** task queues instruction
- **THEN** task unsubscribes immediately after queuing
- **AND** task does not run again in current session

#### Scenario: Skip if first-time install already ran
- **WHEN** task initializes
- **AND** first-time install occurred in current session
- **THEN** task unsubscribes without checking flag
- **AND** no instruction is queued
