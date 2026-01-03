## ADDED Requirements

### Requirement: TaskManager State Machine
The system SHALL provide a TaskManager FSM for coordinating agent communication with callback-based task handling.

#### Scenario: Single active task constraint
- **WHEN** an active task is already running
- **THEN** reject new active task requests until current task completes

#### Scenario: Scheduled task management
- **WHEN** an active task is running
- **THEN** pause all scheduled tasks until active task completes

#### Scenario: Task initiation with protocol
- **WHEN** starting a new task via TaskManager.register_task()
- **THEN** immediately call task.task_start() and set up timeout handling

#### Scenario: Task completion handling
- **WHEN** agent responds via MCP tools
- **THEN** invoke task.response() method to determine next state

#### Scenario: Asyncio timeout handling
- **WHEN** task exceeds its configured timeout period
- **THEN** call task.timeout_expired() and clean up timeout coroutine

#### Scenario: Early task completion
- **WHEN** task completes before timeout expires
- **THEN** cancel the timeout coroutine and clean up resources

### Requirement: Task Protocol Interface
The system SHALL define a Task protocol for standardized task lifecycle management.

#### Scenario: Task protocol methods
- **WHEN** implementing a Task
- **THEN** provide async methods: task_start, response, timeout_expired, completed

#### Scenario: Task timeout configuration
- **WHEN** creating a Task
- **THEN** optionally set timeout attribute for automatic timeout handling

#### Scenario: Task state management
- **WHEN** Task methods are called
- **THEN** return tuple of (next_state, optional_instruction) for coordination

### Requirement: MCP Result Enhancement
The system SHALL extend MCP Result objects to support side-band agent communication.

#### Scenario: Additional instruction field
- **WHEN** returning MCP tool results
- **THEN** optionally include additional_instruction field for agent requests

#### Scenario: Side-band communication
- **WHEN** TaskManager needs to request agent action
- **THEN** piggyback instruction onto next MCP tool response

### Requirement: Agent Communication Tools
The system SHALL provide MCP tools for agents to send workflow state information with task interception.

#### Scenario: Agent sends file information with interception
- **WHEN** agent sends file metadata via MCP tools
- **THEN** route through TaskManager for interested task processing

#### Scenario: Agent sends file content with interception
- **WHEN** agent sends file content via MCP tools
- **THEN** allow interested tasks to process and potentially modify response

#### Scenario: Agent updates workflow state with validation
- **WHEN** agent attempts to modify workflow state file
- **THEN** validate through interested tasks before accepting changes

### Requirement: Generic Task Coordination
The system SHALL provide TaskManager as a generic coordination system not tied to workflow.

#### Scenario: Reusable task management
- **WHEN** implementing coordination for any feature
- **THEN** use TaskManager for consistent task lifecycle management

#### Scenario: Workflow integration
- **WHEN** workflow tracking is enabled
- **THEN** use TaskManager for workflow-specific task coordination

#### Scenario: Future extensibility
- **WHEN** implementing openspec integration or other coordination needs
- **THEN** reuse TaskManager infrastructure
