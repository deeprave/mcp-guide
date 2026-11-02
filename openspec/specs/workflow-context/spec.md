# workflow-context Specification

## Purpose
Define workflow values exposed to Guide templates when workflow tracking is enabled.
## Requirements
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
The template context SHALL expose the established session protocol classification
as `client.protocol` alongside other client-information fields.

#### Scenario: Status with workflow tracking enabled
- **WHEN** user runs `:status` command and `workflow` flag is configured
- **THEN** display current phase, active issue, and queued issues from workflow state file
- **AND** display the connected session's MCP `2026-07-28` or `legacy` protocol
  classification

#### Scenario: Status with workflow tracking disabled
- **WHEN** user runs `:status` command and `workflow` flag is false
- **THEN** display basic project information without workflow details
- **AND** display the connected session's MCP `2026-07-28` or `legacy` protocol
  classification
- **AND** it SHALL NOT instruct the agent to send workflow file content
- **AND** it SHALL NOT imply that workflow monitoring is active

#### Scenario: Status with workflow enabled but state unavailable
- **WHEN** user runs `:status` command and workflow tracking is enabled
- **AND** no workflow state has yet been received
- **THEN** status output SHALL state that workflow state is not yet available
- **AND** SHALL include setup guidance only for the workflow-enabled case
- **AND** SHALL display the connected session's protocol classification

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
- **AND** it SHALL describe `issue` as an optional dash-delimited phrase identifying current work, with no spaces and only filesystem-friendly characters
- **AND** it SHALL describe `plan` as an optional relative path to an existing plan document
- **AND** it SHALL describe `tracking` as an optional single-string external issue-tracker reference
- **AND** it SHALL state that `tracking` is not a mapping
- **AND** it SHALL list only the project's enabled workflow phases as valid `phase` values

#### Scenario: Existing workflow file bootstrap
- **WHEN** a workflow-enabled session starts and the configured workflow file exists
- **THEN** the guidance SHALL provide the strict workflow-file schema
- **AND** it SHALL instruct the agent to read and submit the complete configured file content
- **AND** it SHALL instruct the agent to read the exact configured path directly rather than discover it through a glob, repository search, or tracked-file listing
- **AND** it SHALL list only the project's enabled workflow phases as valid `phase` values

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


### Requirement: Workflow Commands

The workflow command set SHALL provide an explicit command for entering exploration mode.

#### Scenario: Explore command retains current issue
- **WHEN** the user invokes `:workflow/explore` with no issue argument
- **THEN** the workflow phase changes to `exploration`
- **AND** the current issue remains unchanged

#### Scenario: Explore command switches issue explicitly
- **WHEN** the user invokes `:workflow/explore <issue>`
- **THEN** the workflow phase changes to `exploration`
- **AND** the current issue is updated to `<issue>`

#### Scenario: Explore alias is available
- **WHEN** workflow commands are discovered
- **THEN** `:explore` is available as an alias for `:workflow/explore`

### Requirement: Exploratory Issue Suggestion

The workflow system SHALL treat exploratory issue names as a suggestion trigger for exploration mode.

#### Scenario: Exploratory issue suggests exploration mode
- **WHEN** the current issue begins with `explor`
- **THEN** the system suggests entering `exploration`
- **AND** it asks the user for consent before switching
- **AND** it does not switch automatically
