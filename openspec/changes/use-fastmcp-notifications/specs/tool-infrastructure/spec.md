## MODIFIED Requirements

### Requirement: Protocol-specific response adaptation
The common response adapters SHALL use the resolved Session protocol type to
serialise queued additional agent instructions. Legacy responses SHALL preserve
the canonical structured Result payload. MCP `2026-07-28` responses SHALL omit
queued instructions from structured content. When the client negotiated the
Guide instruction-notification extension, the FastMCP request boundary SHALL
dispatch them through that extension and omit them from `_meta`; otherwise the
adapter SHALL use the established response-metadata fallback.

#### Scenario: Modern metadata and structured content are independent
- **WHEN** a modern Session has a queued additional agent instruction
- **AND** the client negotiated the Guide instruction-notification extension
- **THEN** the request boundary SHALL dispatch it through the negotiated
  notification channel when supported
- **AND** the native response SHALL not include the instruction in `_meta`
- **AND** its structured content SHALL not include
  `additional_agent_instructions`

#### Scenario: Modern client lacks notification support
- **WHEN** a modern Session has a queued additional agent instruction
- **AND** the client did not negotiate the Guide instruction-notification extension
- **THEN** the native response SHALL include the instruction in `_meta`
- **AND** its structured content SHALL not include
  `additional_agent_instructions`

#### Scenario: Legacy structured content is unchanged
- **WHEN** a legacy Session adapter receives a Result with an additional agent
  instruction
- **THEN** its structured content SHALL include
  `additional_agent_instructions`
- **AND** it SHALL not add Guide instruction metadata
