## ADDED Requirements

### Requirement: Modern Tool Result Adaptation
The system SHALL convert internal tool `Result` values into SDK-native MCP tool
responses through one protocol adapter. The adapter SHALL preserve result content,
error status, `instruction`, and `additional_agent_instructions` semantics while
placing protocol metadata in the modern response structure.

#### Scenario: Successful tool result
- **WHEN** a tool returns a successful internal result
- **THEN** the protocol adapter SHALL emit a modern tool response with equivalent content and instruction semantics
- **AND** it SHALL not require the tool implementation to serialize a JSON result string for the SDK

#### Scenario: Failed tool result
- **WHEN** a tool returns a failed internal result
- **THEN** the protocol adapter SHALL emit the corresponding modern error/content response
- **AND** the client-visible error and embedded instructions SHALL be retained

### Requirement: Request-Scoped Tool Invocation
The tool registration layer SHALL provide each tool invocation with the application
request context and SHALL not require tool implementations to access a raw FastMCP
context or global active session.

#### Scenario: Project-bound tool invocation
- **WHEN** a project-bound tool receives a request without valid project context
- **THEN** the registration layer SHALL return the no-project result before invoking the tool implementation
- **AND** it SHALL not create or persist a project from server process state
