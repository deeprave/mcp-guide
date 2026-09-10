## ADDED Requirements

### Requirement: Protocol-specific response adaptation
The common response adapters SHALL use the resolved Session protocol type to serialise queued additional agent instructions.  Legacy responses SHALL preserve the canonical structured Result payload.  MCP `2026-07-28` responses SHALL serialise a queued scalar instruction through `_meta["mcp-guide"]["instructions"]` and omit it from the structured payload.

#### Scenario: Modern metadata and structured content are independent
- **WHEN** a modern Session adapter receives a Result with an additional agent instruction
- **THEN** the native response includes the instruction in `_meta`
- **AND** its structured content does not include `additional_agent_instructions`

#### Scenario: Legacy structured content is unchanged
- **WHEN** a legacy Session adapter receives a Result with an additional agent instruction
- **THEN** its structured content includes `additional_agent_instructions`
- **AND** it does not add the Guide instruction metadata value
