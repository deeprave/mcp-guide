## ADDED Requirements

### Requirement: Interactive command resource continuation

The Guide command URI resource path SHALL support an incomplete interactive command
result and a subsequent retry of the same command request. It SHALL preserve the
command path, positional arguments, URI keywords, and previously accepted form
values across the interaction. A command response that needs input SHALL retain the
normal MCP input-result contract rather than serialising it as ordinary command
content.

#### Scenario: Native command resource needs input

- **WHEN** a native `guide://_...` command resource has an applicable unresolved
  elicitation form
- **THEN** its response SHALL be an MCP input-required result
- **AND** its retry SHALL re-enter the same command URI resolution path with the
  accepted values

#### Scenario: Tool-backed command resource needs input

- **WHEN** the `read_resource` tool resolves a `guide://_...` command with an
  applicable unresolved elicitation form
- **THEN** its response SHALL preserve the same MCP input-required result
- **AND** SHALL not adapt it into a normal successful or failed command result

#### Scenario: Prompt command needs input

- **WHEN** the Guide prompt dispatches an underscore-prefixed command with an
  applicable unresolved elicitation form
- **THEN** it SHALL use the same shared command interaction path
- **AND** SHALL preserve the prompt's existing project-binding and command
  argument semantics
