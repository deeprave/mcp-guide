## ADDED Requirements

### Requirement: Tool façade invokes a Guide skill through shared resolution
The system SHALL expose `{{tool_prefix}}use_skill` as a project-dependent MCP
tool registered through `@toolfunc`. Its first argument SHALL be a plain Guide
skill name, with or without a leading `$`; it SHALL NOT be a URI. Its optional
`args` list SHALL be parsed using the shared Guide command-argument parser,
with the skill name as argv[0]. It SHALL resolve only an exact effective skill
identifier and SHALL NOT duplicate the skill's argument,
elicitation, policy, rendering, or response-handling behaviour at the MCP tool
layer.

#### Scenario: Tool invokes a skill with arguments
- **WHEN** a bound client calls `{{tool_prefix}}use_skill` for
  `workflow-review` with `args: ["mode=uncommitted", "verbose"]`
- **THEN** the resolved skill receives `mode` with value `uncommitted` and
  `verbose` with value `true` through its keyword template context
- **AND** the tool uses the shared command-argument parser rather than duplicating it

#### Scenario: Tool rejects a skill member path
- **WHEN** a client calls `{{tool_prefix}}use_skill` with a skill member path
- **THEN** it receives the ordinary no-such-skill result

#### Scenario: Tool accepts the optional skill marker
- **WHEN** a bound client calls `{{tool_prefix}}use_skill` for
  `$workflow-review`
- **THEN** it resolves the `workflow-review` Guide skill

#### Scenario: Tool is called without a project
- **WHEN** an unbound client calls `{{tool_prefix}}use_skill`
- **THEN** it receives the standard no-project result used by other
  project-dependent tools
