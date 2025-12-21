# Template Support Specification Changes

## MODIFIED Requirements

### Requirement: Template Context Variables
The template system SHALL provide access to agent and environment information through context variables including agent name, version, prompt character, and tool prefix.

#### Scenario: Agent information in templates
- GIVEN a template is being rendered
- WHEN agent information is needed
- THEN the template context SHALL include:
  - `agent_name`: The normalized agent name
  - `agent_version`: The agent version (if available)
  - `@`: The prompt character for the agent
  - `tool_prefix`: The MCP tool prefix with underscore separator

#### Scenario: Tool prefix from environment
- GIVEN MCP_TOOL_PREFIX environment variable is set to "custom"
- WHEN template context is built
- THEN `tool_prefix` SHALL be "custom_"

#### Scenario: Default tool prefix
- GIVEN MCP_TOOL_PREFIX is not set or is "guide"
- WHEN template context is built
- THEN `tool_prefix` SHALL be "guide_"

#### Scenario: Tool reference in templates
- GIVEN a template needs to reference an MCP tool
- WHEN using `{{tool_prefix}}get_content`
- THEN it SHALL resolve to the correct tool name (e.g., "guide_get_content")

## ADDED Requirements

### Requirement: Dynamic Tool References
Templates SHALL support dynamic tool name construction using the tool_prefix variable.

#### Scenario: Portable tool references
- GIVEN a template references `{{tool_prefix}}tool_name`
- WHEN rendered with different MCP_TOOL_PREFIX values
- THEN the tool reference SHALL adapt to the configured prefix
- AND maintain correct underscore separation
