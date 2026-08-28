## ADDED Requirements

### Requirement: Request-Scoped Prompt Invocation
The prompt registration layer SHALL invoke prompts with the application request
context and SHALL resolve project, client, and agent data from that context rather
than legacy initialization/session fields.

#### Scenario: Prompt with project context
- **WHEN** a negotiated prompt request supplies valid project context
- **THEN** the prompt SHALL render using that request's project, agent, and client data
- **AND** concurrent prompt requests SHALL not share those values

#### Scenario: Prompt without project context
- **WHEN** a prompt request has no valid project context
- **THEN** the prompt infrastructure SHALL use its defined unbound behavior
- **AND** it SHALL not infer a project from server cwd or a previous connection,
  except for the defined one-time inherited-`PWD` bootstrap of an unbound stdio interaction

### Requirement: Modern Prompt Result Adaptation
The prompt registration layer SHALL return SDK-native modern prompt responses through
the common result adapter while preserving rendered instruction dispositions and safe
protocol metadata.

#### Scenario: Prompt returns rendered instruction
- **WHEN** a prompt produces rendered content with an embedded instruction disposition
- **THEN** the response SHALL preserve that disposition through the modern MCP result
- **AND** protocol metadata SHALL not be encoded only in prompt text
