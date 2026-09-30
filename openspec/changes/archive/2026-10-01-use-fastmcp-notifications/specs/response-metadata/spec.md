## MODIFIED Requirements

### Requirement: Modern side-band instruction metadata
The system SHALL deliver a queued scalar additional agent instruction for an MCP
`2026-07-28` Session through the negotiated Guide instruction-notification
extension when the client supports it. A modern client that does not negotiate
the extension SHALL receive the instruction through the established
`_meta["mcp-guide"]["instructions"]` fallback.

#### Scenario: Modern instruction accompanies a success result
- **WHEN** a session has queued additional agent instructions and a tool returns
  a successful result
- **AND** the Session protocol type is `mcp_2026_07_28`
- **AND** the client negotiated the Guide instruction-notification extension
- **THEN** Guide SHALL dispatch the queued instruction through the negotiated
  notification channel when the client supports it
- **AND** the structured Guide result SHALL not contain
  `additional_agent_instructions`
- **AND** the response `_meta` SHALL not contain `mcp-guide.instructions`

#### Scenario: Modern instruction accompanies a failure result
- **WHEN** a session has queued additional agent instructions and a tool returns
  a failure result
- **AND** the Session protocol type is `mcp_2026_07_28`
- **AND** the client negotiated the Guide instruction-notification extension
- **THEN** the failure result SHALL remain otherwise unchanged
- **AND** the response `_meta` SHALL not contain a queued instruction

#### Scenario: Legacy instruction remains in the result
- **WHEN** a Session has a legacy protocol type and an outgoing result contains
  an additional agent instruction
- **THEN** the structured Guide result SHALL contain
  `additional_agent_instructions`
- **AND** the response SHALL not add the Guide instruction metadata value

### Requirement: Public-surface metadata consistency
The system SHALL preserve the protocol-specific instruction contract through
tool, prompt, and resource response adapters. A negotiated modern client SHALL
receive no Guide instruction key in response metadata; a modern client without
the notification extension SHALL receive the established metadata fallback.
Cache metadata SHALL remain independent.

#### Scenario: Prompt delivery
- **WHEN** a modern prompt response has a queued instruction
- **AND** the client negotiated the Guide instruction-notification extension
- **THEN** its native response `_meta` SHALL not contain a Guide instruction
- **AND** queued delivery SHALL use the negotiated notification channel when
  supported

#### Scenario: Resource delivery
- **WHEN** a modern resource response has a queued instruction
- **AND** the client negotiated the Guide instruction-notification extension
- **THEN** its native response `_meta` SHALL not contain a Guide instruction
- **AND** queued delivery SHALL use the negotiated notification channel when
  supported

#### Scenario: No queued instructions
- **WHEN** an outgoing modern response has no queued additional agent instruction
- **THEN** it SHALL not contain `mcp-guide.instructions`

#### Scenario: Modern client falls back without notification support
- **WHEN** a modern Session has a queued additional agent instruction
- **AND** the client did not negotiate the Guide instruction-notification extension
- **THEN** the response `_meta` SHALL contain the instruction at
  `mcp-guide.instructions`
- **AND** the structured Guide result SHALL not contain
  `additional_agent_instructions`
