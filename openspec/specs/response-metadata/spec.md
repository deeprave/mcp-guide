# response-metadata Specification

## Purpose
Guide responses need a standard side-band channel for session-generated instructions in the current MCP protocol while preserving retained-client compatibility.

## Requirements

### Requirement: Modern side-band instruction metadata
The system SHALL deliver a queued scalar additional agent instruction for an MCP `2026-07-28` Session through `_meta["mcp-guide"]["instructions"]`.  The metadata value SHALL be omitted when no instruction is queued.

#### Scenario: Modern instruction accompanies a success result
- **WHEN** a session has queued additional agent instructions and a tool returns a successful result
- **AND** the Session protocol type is `mcp_2026_07_28`
- **THEN** the response `_meta` contains its next queued instruction at `mcp-guide.instructions`
- **AND** the structured Guide result does not contain `additional_agent_instructions`

#### Scenario: Modern instruction accompanies a failure result
- **WHEN** a session has queued additional agent instructions and a tool returns a failure result
- **AND** the Session protocol type is `mcp_2026_07_28`
- **THEN** the failure result remains otherwise unchanged
- **AND** the response `_meta` contains the scalar instruction

#### Scenario: Legacy instruction remains in the result
- **WHEN** a Session has a legacy protocol type and an outgoing result contains an additional agent instruction
- **THEN** the structured Guide result contains `additional_agent_instructions`
- **AND** the response does not add the Guide instruction metadata value

### Requirement: Public-surface metadata consistency
The system SHALL preserve the protocol-specific instruction contract through tool, prompt, and resource response adapters.  A modern response with no queued instruction SHALL not include an empty Guide metadata namespace or instruction key.

#### Scenario: Prompt delivery
- **WHEN** a prompt response has queued side-band metadata
- **AND** its Session protocol type is `mcp_2026_07_28`
- **THEN** its native response `_meta` contains the Guide metadata value

#### Scenario: Resource delivery
- **WHEN** a resource response has queued side-band metadata
- **AND** its Session protocol type is `mcp_2026_07_28`
- **THEN** its native response `_meta` contains the Guide metadata value

#### Scenario: No queued instructions
- **WHEN** an outgoing modern response has no queued additional agent instruction
- **THEN** it does not contain `mcp-guide.instructions`
