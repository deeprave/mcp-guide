## Purpose

Guide responses need a separate, explicit channel for session-generated side-band information that is unrelated to the result it accompanies.

## ADDED Requirements

### Requirement: Side-band response metadata
The system SHALL model response metadata separately from the Guide result payload.  Response metadata SHALL carry information that is independent of the result value, success, failure, instruction, and disposition.

#### Scenario: Result-specific instruction remains in the result
- **WHEN** a result includes an instruction describing how to handle its content
- **THEN** that instruction remains in the result payload
- **AND** it is not converted to response metadata

### Requirement: Queued agent-instruction list delivery
The system SHALL deliver every session-queued additional agent instruction with the next outgoing response.  It SHALL remove the queued instructions in FIFO order and attach them as the `mcp-guide/additional_agent_instructions` `_meta` list, independently of the result payload.  List order SHALL express only delivery sequence, not priority or required action order.

#### Scenario: Queued instructions accompany a success result
- **WHEN** a session has queued additional agent instructions and a tool returns a successful result
- **THEN** the result payload contains only result-specific fields
- **AND** the response `_meta` contains the queued instructions as a list

#### Scenario: Queued instructions accompany a failure result
- **WHEN** a session has queued additional agent instructions and a tool returns a failure result
- **THEN** the failure result remains unchanged
- **AND** the response `_meta` contains the queued instructions as a list

#### Scenario: Multiple queued instructions
- **WHEN** a session has multiple queued additional agent instructions
- **THEN** the current response metadata contains every queued instruction in FIFO order
- **AND** the queue is empty after those instructions are attached

### Requirement: Public-surface metadata consistency
The system SHALL preserve resolved response metadata through tool, prompt, and resource response adapters.  A response with no side-band metadata SHALL not include an empty Guide side-band metadata value.

#### Scenario: Prompt delivery
- **WHEN** a prompt response has queued side-band metadata
- **THEN** its native response `_meta` contains the Guide metadata value

#### Scenario: Resource delivery
- **WHEN** a resource response has queued side-band metadata
- **THEN** its native response `_meta` contains the Guide metadata value

#### Scenario: No queued instructions
- **WHEN** an outgoing response has no queued additional agent instruction
- **THEN** it does not contain `mcp-guide/additional_agent_instructions`

### Requirement: No result-payload duplication
The system SHALL NOT serialise `additional_agent_instructions` in a Guide `Result` payload or embed it within `guide_result` metadata.

#### Scenario: Structured tool result
- **WHEN** a tool response includes queued additional agent instructions
- **THEN** its structured Guide result does not contain `additional_agent_instructions`
- **AND** the instruction is available only through response metadata
