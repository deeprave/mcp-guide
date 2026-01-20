## ADDED Requirements

### Requirement: Workflow Template Context
The system SHALL provide workflow-related variables in template context when workflow tracking is enabled.

#### Scenario: Current workflow phase
- **WHEN** rendering templates with workflow tracking enabled
- **THEN** include `workflow_phase` variable with current phase name

#### Scenario: Next workflow phase
- **WHEN** rendering templates with workflow tracking enabled
- **THEN** include `workflow_next` variable with next phase based on list order

#### Scenario: Workflow file path
- **WHEN** rendering templates with workflow tracking enabled
- **THEN** include `workflow_file` variable with workflow state file name/path

#### Scenario: Current workflow task
- **WHEN** rendering templates with workflow tracking enabled
- **THEN** include `workflow_task` variable with current issue name

#### Scenario: Workflow task description
- **WHEN** rendering templates with workflow tracking enabled
- **THEN** include `workflow_description` variable with task description (may be blank)

### Requirement: Workflow State Monitoring and Caching
The system SHALL monitor workflow state file changes and cache state for template context.

#### Scenario: Workflow state file monitoring
- **WHEN** workflow tracking is enabled
- **THEN** monitor workflow state file for changes using WorkflowMonitorTask

#### Scenario: Workflow state caching
- **WHEN** workflow state file changes are detected
- **THEN** parse content into WorkflowState model and cache in TaskManager

#### Scenario: State change detection
- **WHEN** workflow state changes
- **THEN** queue additional_instruction to notify agent of state transition

### Requirement: Agent Instruction System
The system SHALL provide template-based workflow instructions to guide agent behavior.

#### Scenario: Workflow instruction directory
- **WHEN** workflow tracking is enabled
- **THEN** serve instructions from docroot/_workflow/ directory as templates

#### Scenario: Template-based instructions
- **WHEN** serving workflow instructions
- **THEN** process instructions as templates with frontmatter support including requires-* conditions

#### Scenario: Proactive agent guidance
- **WHEN** workflow state changes
- **THEN** send appropriate instruction templates via additional_instruction field

### Requirement: Response Processing Extension
The system SHALL extend tool decorator pattern to process all agent responses for instruction injection.

#### Scenario: Prompt response processing
- **WHEN** agent sends any response (not just tool calls)
- **THEN** process response through TaskManager for additional_instruction injection

#### Scenario: Global instruction injection
- **WHEN** TaskManager has pending instructions
- **THEN** inject instructions into all agent interactions via additional_instruction

### Requirement: Separate Workflow Context
The system SHALL maintain workflow context separate from project context with independent lifecycle.

#### Scenario: Workflow context isolation
- **WHEN** building template context
- **THEN** create separate workflow context scope with workflow.* variables

#### Scenario: Workflow context invalidation
- **WHEN** workflow state changes
- **THEN** invalidate workflow context cache independently of project context

#### Scenario: Workflow context integration
- **WHEN** rendering templates
- **THEN** merge workflow context with existing template context

### Requirement: Enhanced Partial Support
The system SHALL support frontmatter conditions in template partials for conditional rendering.

#### Scenario: Partial frontmatter processing
- **WHEN** rendering template partials
- **THEN** process frontmatter including requires-* conditions

#### Scenario: Conditional partial rendering
- **WHEN** partial has requires-* frontmatter
- **THEN** only render partial if requirements are satisfied

#### Scenario: Status template workflow section
- **WHEN** rendering status template with workflow enabled
- **THEN** conditionally include workflow information section

### Requirement: Workflow Status Display
The system SHALL update status command to show workflow information when enabled.

#### Scenario: Status with workflow tracking enabled
- **WHEN** user runs `:status` command and `workflow` flag is configured
- **THEN** display current phase, active issue, and queued issues from workflow state file

#### Scenario: Status with workflow tracking disabled
- **WHEN** user runs `:status` command and `workflow` flag is false
- **THEN** display basic project information without workflow details

### Requirement: Workflow Command Integration
The system SHALL provide workflow-related commands integrated into existing command templates.

#### Scenario: Workflow status command
- **WHEN** workflow tracking is enabled
- **THEN** provide commands to show current workflow status and available transitions

#### Scenario: Phase transition commands
- **WHEN** workflow tracking is enabled
- **THEN** provide commands for phase transitions, issue management, and queue management

#### Scenario: Configuration-aware commands
- **WHEN** serving workflow commands
- **THEN** make commands sensitive to current workspace configuration and state file location
