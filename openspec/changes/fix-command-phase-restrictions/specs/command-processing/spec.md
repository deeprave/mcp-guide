## ADDED Requirements

### Requirement: Command Phase Restriction Enforcement
The command processing system SHALL properly enforce `requires-workflow-phase` restrictions by either blocking commands completely or allowing full execution.

#### Scenario: Command blocked in wrong phase
- **WHEN** a command with `requires-workflow-phase: [discussion, planning]` is executed in `review` phase
- **THEN** the command SHALL be completely blocked with a clear error message
- **AND** no help text or partial execution SHALL occur

#### Scenario: Command allowed in correct phase
- **WHEN** a command with `requires-workflow-phase: [discussion, planning]` is executed in `discussion` phase
- **THEN** the command SHALL execute normally and process all arguments
- **AND** no phase-related restrictions SHALL interfere with execution

### Requirement: Consistent Requires Directive Behavior
All `requires-*` directives SHALL have consistent enforcement behavior across the command processing system.

#### Scenario: Multiple requires directives
- **WHEN** a command has multiple `requires-*` directives (e.g., `requires-workflow` and `requires-workflow-phase`)
- **THEN** all restrictions SHALL be evaluated
- **AND** the command SHALL be blocked if any restriction fails
- **AND** appropriate error messages SHALL indicate which restriction failed

## MODIFIED Requirements

### Requirement: Command Error Messaging
The command processing system SHALL provide clear, actionable error messages when commands are blocked due to restrictions.

#### Scenario: Phase restriction error message
- **WHEN** a command is blocked due to phase restrictions
- **THEN** the error message SHALL indicate the current phase and allowed phases
- **AND** the message SHALL suggest when the command can be used
- **EXAMPLE**: "Command ':issue' requires workflow phase [discussion, planning] but current phase is 'review'. Use this command during discussion or planning phases."
