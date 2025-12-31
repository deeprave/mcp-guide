## ADDED Requirements

### Requirement: Project Status Tracking
The system SHALL provide project workflow status tracking through a structured `.guide` file when the `phase-tracking` project flag is enabled.

#### Scenario: Status display with phase tracking enabled
- **WHEN** user runs `:status` command and `phase-tracking` flag is true
- **THEN** display current phase, active issue, and queued issues from `.guide` file

#### Scenario: Status display with phase tracking disabled
- **WHEN** user runs `:status` command and `phase-tracking` flag is false
- **THEN** display basic project information without workflow details

### Requirement: Guide File Format
The system SHALL support a structured YAML format for the `.guide` file with phase and issue tracking.

#### Scenario: Valid guide file structure
- **WHEN** `.guide` file exists with valid YAML structure
- **THEN** parse phase, current issue, and issue queue successfully

#### Scenario: Guide file format validation
- **WHEN** `.guide` file has invalid structure
- **THEN** provide clear error messages and fallback gracefully

### Requirement: Agent Guide Management
The system SHALL provide MCP tools for agents to read and update the `.guide` file for workflow management.

#### Scenario: Agent reads current status
- **WHEN** agent requests current project status
- **THEN** return parsed `.guide` file content with phase and issues

#### Scenario: Agent updates issue queue
- **WHEN** agent needs to add/remove/reorder issues
- **THEN** provide tools to safely modify `.guide` file structure

### Requirement: Phase-Based Instructions
The system SHALL include phase-specific instructions in documentation content when `phase-tracking` is enabled.

#### Scenario: Phase-aware documentation
- **WHEN** retrieving category content with phase tracking enabled
- **THEN** include relevant phase instructions from tracking documentation
