## ADDED Requirements

### Requirement: WorkflowManager State Machine
The system SHALL provide a WorkflowManager FSM for coordinating agent communication with callback-based task handling.

#### Scenario: Single active task constraint
- **WHEN** a task is already active
- **THEN** reject new task requests until current task completes

#### Scenario: Task initiation with callback
- **WHEN** starting a new task via `start_task(callback)`
- **THEN** transition to appropriate state and return agent instructions

#### Scenario: Task completion handling
- **WHEN** agent responds via MCP tools
- **THEN** invoke callback with received content to determine next state

#### Scenario: Task timeout handling
- **WHEN** task exceeds timeout period
- **THEN** notify agent and reset to idle state

### Requirement: Agent Communication Tools
The system SHALL provide MCP tools for agents to send workflow state information.

#### Scenario: Agent sends file information
- **WHEN** agent requests information about workflow file path
- **THEN** provide tools to send file metadata (mtime, size, existence)

#### Scenario: Agent sends file content
- **WHEN** agent requests workflow file content
- **THEN** provide tools to send file content via MCP

#### Scenario: Agent updates workflow state
- **WHEN** agent needs to modify workflow state file
- **THEN** provide tools to safely update workflow structure

### Requirement: Minimal User Interaction
The system SHALL minimize user interaction for workflow state monitoring.

#### Scenario: Automatic state monitoring
- **WHEN** workflow tracking is enabled
- **THEN** automatically request state updates from agent with minimal user prompts

#### Scenario: Guide prompt integration
- **WHEN** guide prompt is available
- **THEN** include workflow monitoring instructions in guide content

#### Scenario: Proactive state requests
- **WHEN** workflow operations are needed
- **THEN** issue agent instructions through available channels with minimal user interaction
