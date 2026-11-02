# Spec Delta

## MODIFIED Requirements

### Requirement: Workflow State-Format Template Guidance
The workflow state-format template SHALL render agent instructions headed “Workflow State File Format” that describe a strictly YAML workflow-file structure with lowercase keys and use `send_file_content` as the exact MCP tool name for returning the complete updated workflow file. It SHALL describe `issue` as a dash-delimited, filesystem-friendly phrase identifying current work, `plan` as a relative path to an existing plan document, and `tracking` as a single-string external issue-tracker reference.

#### Scenario: Required and optional state fields
- **WHEN** the workflow state-format template is rendered
- **THEN** it SHALL present `phase` as required
- **AND** it SHALL identify `issue`, `plan`, `tracking`, `description`, and `queue` as optional as applicable
- **AND** it SHALL describe `description` as an optional description
- **AND** it SHALL state that optional lines may be omitted
- **AND** it SHALL state that keys use lowercase names

#### Scenario: Active change and tracking guidance
- **WHEN** the workflow state-format template or workflow discussion guidance is rendered
- **THEN** it SHALL identify `issue` as the field for the dash-delimited, filesystem-friendly current-work phrase
- **AND** it SHALL identify `tracking` as an optional external issue-tracker reference
- **AND** it SHALL state that `tracking` is a single string rather than a mapping
- **AND** it SHALL direct an OpenSpec-enabled project to record an active OpenSpec change in `issue`, not `tracking`

#### Scenario: Empty queue and update instruction
- **WHEN** the workflow state-format template is rendered
- **THEN** it SHALL state that an empty queue is omitted
- **AND** it SHALL instruct the agent to update `{{workflow.file}}`
- **AND** it SHALL instruct the agent to use `send_file_content` as the exact MCP tool name
- **AND** it SHALL not include a generic phase-transition reminder
