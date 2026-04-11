## MODIFIED Requirements

### Requirement: Document Add Command

The `:document/add` command SHALL support a handoff-capable execution path for clients that expose `agent.has_handoff`, while retaining a universal inline fallback path.

The command SHALL continue to preserve the same `send_file_content` semantics and argument handling as the existing command.

#### Scenario: Handoff-capable client uses separate execution
- **WHEN** `:document/add` is rendered for a client with `agent.has_handoff=true`
- **THEN** the template instructs the agent to use separate execution when it can still complete the workflow end-to-end
- **AND** the workflow still ends with `send_file_content`

#### Scenario: Inline fallback remains universal
- **WHEN** `:document/add` is rendered for a client with `agent.has_handoff=false`
- **THEN** the template instructs the agent to perform the workflow inline

#### Scenario: Standardized fallback wording
- **WHEN** the handoff-oriented path cannot actually be used
- **THEN** the agent uses standardized fallback explanation wording before continuing inline
