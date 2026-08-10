## ADDED Requirements

### Requirement: Workflow State-Format Template Guidance
The workflow state-format template SHALL render agent instructions headed “Workflow State File Format” that describe a strictly YAML workflow-file structure with lowercase keys and use `send_file_content` as the exact MCP tool name for returning the complete updated workflow file.

#### Scenario: Required and optional state fields
- **WHEN** the workflow state-format template is rendered
- **THEN** it SHALL present `phase` as required
- **AND** it SHALL identify `issue`, `tracking`, `description`, and `queue` as optional as applicable
- **AND** it SHALL describe `description` as an optional description
- **AND** it SHALL state that optional lines may be omitted
- **AND** it SHALL state that keys use lowercase names

#### Scenario: Active change and tracking guidance
- **WHEN** the workflow state-format template is rendered
- **THEN** it SHALL state that `issue` is required for an active change
- **AND** it SHALL state that `tracking` is required when an active change has an assigned external issue
- **AND** it SHALL state that the tracker prefix is optional and the tracker identifier is the required tracking value

#### Scenario: Empty queue and update instruction
- **WHEN** the workflow state-format template is rendered
- **THEN** it SHALL state that an empty queue is omitted
- **AND** it SHALL instruct the agent to update `{{workflow.file}}`
- **AND** it SHALL instruct the agent to use `send_file_content` as the exact MCP tool name
- **AND** it SHALL not include a generic phase-transition reminder
